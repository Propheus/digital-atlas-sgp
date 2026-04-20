"""
Merlion FastAPI backend.

Exposes the merlion package as a thin HTTP service.

Endpoints:
  GET  /                       health check
  GET  /api/use_cases          list registered use cases
  GET  /api/audit              routing chain audit
  POST /api/ask                natural language → routed result
  POST /api/run                direct use case call

Run:
  cd merlion-app/backend && uvicorn server:app --host 0.0.0.0 --port 18700 --reload
"""
import os
import sys
from typing import Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure merlion package is importable (one level up)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)

# Load env for ANTHROPIC_API_KEY
env_path = os.path.join(REPO_ROOT, "merlion", ".env")
if os.path.exists(env_path):
    for line in open(env_path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from merlion import Merlion  # noqa: E402
from merlion.models.registry import validate_paths  # noqa: E402


app = FastAPI(
    title="Real World Engine",
    version="0.1.0",
    description=(
        "Real World Engine — SGP urban intelligence orchestrator. "
        "Classifies natural-language queries, routes to the right model "
        "(GCN, Node2Vec, UMAP, XGBoost), executes, returns grounded answers."
    ),
)

# CORS: allow local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared Merlion instance (loads LLM backend once)
_merlion = Merlion(use_llm=True)


class AskRequest(BaseModel):
    query: str
    top_n: int = 3


class RunRequest(BaseModel):
    use_case: str
    params: dict[str, Any] = {}


@app.get("/")
def health():
    return {
        "service": "real-world-engine",
        "name": "Real World Engine",
        "powered_by": "merlion",
        "status": "ok",
        "version": "0.1.0",
        "description": (
            "SGP urban intelligence orchestrator — natural language → "
            "use case → model execution over 7,318 hex embeddings."
        ),
    }


@app.get("/api/use_cases")
def use_cases():
    return {"use_cases": _merlion.use_cases()}


@app.get("/api/audit")
def audit():
    """Full routing chain audit: use_case → model → dataset."""
    paths = validate_paths()
    ucs = _merlion.use_cases()
    return {
        "use_cases": ucs,
        "model_datasets": paths,
        "all_datasets_present": all(p["exists"] for p in paths.values()),
    }


@app.post("/api/ask")
def ask(req: AskRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")
    try:
        result = _merlion.ask(req.query, top_n=req.top_n)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/run")
def run(req: RunRequest):
    try:
        return _merlion.run(req.use_case, **req.params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
