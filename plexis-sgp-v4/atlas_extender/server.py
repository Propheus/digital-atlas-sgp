"""Atlas Extender — FastAPI server with SSE streaming.

Endpoints:
  GET  /                  → UI
  POST /run               → starts a run, returns run_id
  GET  /stream/{run_id}   → SSE stream of events for that run
  GET  /runs              → list past runs
  GET  /runs/{run_id}     → fetch artifacts of a finished run
  GET  /artifact/{run_id}/{name}  → fetch any file from extension dir

Run with:
  uvicorn atlas_extender.server:app --host 0.0.0.0 --port 18900
"""
import asyncio
import json
import threading
import time
import uuid
from pathlib import Path
from queue import Queue, Empty
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .agents.builder import ROOT
from .pipeline_v2 import extend_v2_stream

app = FastAPI(title="Plexis Atlas Extender")

# In-memory run registry (run_id → state)
_runs: dict = {}

UI_PATH = Path(__file__).parent / "ui"


class RunRequest(BaseModel):
    use_case: str


@app.get("/", response_class=HTMLResponse)
def index():
    p = UI_PATH / "index.html"
    if p.exists():
        return HTMLResponse(p.read_text())
    return HTMLResponse("<h1>UI not built — see /ui/index.html</h1>")


@app.get("/static/{filename}")
def static(filename: str):
    p = UI_PATH / filename
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p)


@app.post("/run")
def start_run(req: RunRequest):
    """Start a new pipeline run. Returns run_id immediately; events stream via SSE."""
    run_id = uuid.uuid4().hex[:12]
    queue = Queue()
    _runs[run_id] = {
        "id": run_id,
        "use_case": req.use_case,
        "status": "running",
        "queue": queue,
        "events": [],   # accumulated for replay
        "started": time.time(),
        "output_dir": None,
    }

    def worker():
        try:
            for event in extend_v2_stream(req.use_case):
                _runs[run_id]["events"].append(event)
                queue.put(event)
                if event.get("stage") == "init":
                    _runs[run_id]["output_dir"] = event["payload"]["output_dir"]
                if event.get("stage") in ("done", "error"):
                    _runs[run_id]["status"] = "done" if event["stage"] == "done" else "error"
        except Exception as e:
            err_evt = {"stage": "error", "status": "fail", "payload": {"error": str(e)}}
            _runs[run_id]["events"].append(err_evt)
            queue.put(err_evt)
            _runs[run_id]["status"] = "error"
        finally:
            queue.put(None)  # sentinel

    threading.Thread(target=worker, daemon=True).start()
    return {"run_id": run_id, "status": "running"}


@app.get("/stream/{run_id}")
def stream(run_id: str):
    """Server-Sent Events stream of pipeline events for a given run."""
    if run_id not in _runs:
        raise HTTPException(404)
    run = _runs[run_id]
    queue = run["queue"]

    def gen():
        # Replay any events that already happened (for late-connecting clients)
        for evt in run["events"]:
            yield f"data: {json.dumps(evt)}\n\n"
        # Then stream live
        while True:
            try:
                evt = queue.get(timeout=300)
            except Empty:
                yield f": keepalive\n\n"
                continue
            if evt is None:
                break
            yield f"data: {json.dumps(evt)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.get("/runs")
def list_runs():
    out = []
    for run_id, run in sorted(_runs.items(), key=lambda kv: -kv[1]["started"]):
        out.append({
            "run_id": run_id,
            "use_case": run["use_case"][:120],
            "status": run["status"],
            "started": run["started"],
            "output_dir": run.get("output_dir"),
            "n_events": len(run["events"]),
        })
    # Also list saved runs from disk (extensions/v2-*)
    ext_dir = ROOT / "extensions"
    if ext_dir.exists():
        for d in sorted(ext_dir.glob("v2-*"), key=lambda p: -p.stat().st_mtime):
            rep_path = d / "0_report.json"
            if not rep_path.exists():
                continue
            run_id = d.name
            if run_id in [r["run_id"] for r in out]:
                continue
            try:
                rep = json.load(open(rep_path))
                out.append({
                    "run_id": run_id,
                    "use_case": rep.get("use_case", "")[:120],
                    "status": "done" if rep.get("n_added") is not None else "unknown",
                    "started": d.stat().st_mtime,
                    "output_dir": str(d),
                    "n_added": rep.get("n_added"),
                })
            except Exception:
                pass
    return out


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    if run_id in _runs:
        run = _runs[run_id]
        return {
            "run_id": run_id,
            "use_case": run["use_case"],
            "status": run["status"],
            "events": run["events"],
            "output_dir": run.get("output_dir"),
        }
    # Try disk
    p = ROOT / "extensions" / run_id
    if p.exists() and (p / "0_report.json").exists():
        return {
            "run_id": run_id,
            "use_case": json.load(open(p / "0_report.json")).get("use_case", ""),
            "status": "done",
            "events": [],
            "output_dir": str(p),
        }
    raise HTTPException(404)


@app.get("/artifact/{run_id}/{name}")
def get_artifact(run_id: str, name: str):
    """Fetch any file from the run's output directory."""
    out_dir = None
    if run_id in _runs:
        out_dir = _runs[run_id].get("output_dir")
    if not out_dir:
        out_dir = ROOT / "extensions" / run_id
    p = Path(out_dir) / name
    if not p.exists():
        raise HTTPException(404, f"No artifact {name}")
    if name.endswith(".json"):
        return JSONResponse(json.load(open(p)))
    if name.endswith(".md"):
        return HTMLResponse(p.read_text(), media_type="text/markdown")
    return FileResponse(p)


@app.get("/health")
def health():
    return {"ok": True, "n_runs": len(_runs)}
