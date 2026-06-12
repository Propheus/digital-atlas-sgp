#!/usr/bin/env python3
"""
Plexis-Mind store service — conversations + feedback persistence, and (flagged)
session memory. Runs SEPARATE from the GPU model process so a model crash can
never corrupt durable user data. Pure stdlib sqlite3 + FastAPI.

Run:  PORT=8091 python3 store_server.py
Env:  STORE_DB (/root/plexis_chat.db), MEMORY_ENABLED (false),
      MEMORY_OBSERVATORY_PATH (/root/memory-observatory), MEMORY_DB (/root/plexis_memory.db)
"""
import os, sqlite3, time, uuid, json, sys
from contextlib import closing
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

DB   = os.environ.get("STORE_DB", "/root/plexis_chat.db")
PORT = int(os.environ.get("PORT", "8091"))

def _conn():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL"); return c

def _init():
    with closing(_conn()) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS conversations(
            id TEXT PRIMARY KEY, client TEXT, title TEXT,
            created_at REAL, updated_at REAL);
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT, conv_id TEXT, idx INTEGER,
            role TEXT, content TEXT, entity TEXT, grounded INTEGER, ts REAL);
        CREATE TABLE IF NOT EXISTS feedback(
            id INTEGER PRIMARY KEY AUTOINCREMENT, conv_id TEXT, msg_idx INTEGER,
            vote TEXT, note TEXT, question TEXT, answer TEXT, entity TEXT, ts REAL);
        CREATE INDEX IF NOT EXISTS ix_msg_conv ON messages(conv_id);
        CREATE INDEX IF NOT EXISTS ix_conv_client ON conversations(client);
        """)
        c.commit()
_init()

# ----------------------------------------------------------- session memory (flagged)
try:
    import kb_memory as MEM          # local adapter that borrows the observatory
    MEM_OK = MEM.is_enabled()
except Exception as e:               # noqa: BLE001
    MEM, MEM_OK = None, False
    print(f"[store] memory adapter unavailable: {e}", flush=True)

app = FastAPI(title="Plexis-Mind Store")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Msg(BaseModel):
    role: str; content: str
    entity: str | None = None
    grounded: bool | None = None

class SaveReq(BaseModel):
    id: str | None = None
    client: str = "default"
    title: str | None = None
    messages: list[Msg] = []

class FeedbackReq(BaseModel):
    conv_id: str | None = None
    msg_idx: int = 0
    vote: str                         # "up" | "down"
    note: str | None = None
    question: str | None = None
    answer: str | None = None
    entity: str | None = None

@app.get("/health")
def health():
    with closing(_conn()) as c:
        n = c.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        f = c.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    return {"status": "ok", "conversations": n, "feedback": f, "memory": MEM_OK}

@app.get("/conversations")
def list_convs(client: str = "default"):
    with closing(_conn()) as c:
        rows = c.execute("""
            SELECT cv.id, cv.title, cv.updated_at,
                   (SELECT COUNT(*) FROM messages m WHERE m.conv_id=cv.id) AS n
            FROM conversations cv WHERE cv.client=?
            ORDER BY cv.updated_at DESC LIMIT 200""", (client,)).fetchall()
    return [{"id": r["id"], "title": r["title"], "updated_at": r["updated_at"], "messages": r["n"]} for r in rows]

@app.get("/conversations/{cid}")
def get_conv(cid: str):
    with closing(_conn()) as c:
        cv = c.execute("SELECT * FROM conversations WHERE id=?", (cid,)).fetchone()
        if not cv: return JSONResponse({"error": "not_found"}, status_code=404)
        ms = c.execute("SELECT role,content,entity,grounded FROM messages WHERE conv_id=? ORDER BY idx", (cid,)).fetchall()
    return {"id": cv["id"], "title": cv["title"],
            "messages": [{"role": m["role"], "content": m["content"],
                          "entity": m["entity"], "grounded": bool(m["grounded"])} for m in ms]}

@app.post("/conversations")
def save_conv(req: SaveReq):
    cid = req.id or uuid.uuid4().hex[:12]
    now = time.time()
    title = (req.title or (req.messages[0].content if req.messages else "New chat"))[:80]
    with closing(_conn()) as c:
        ex = c.execute("SELECT id FROM conversations WHERE id=?", (cid,)).fetchone()
        if ex:
            c.execute("UPDATE conversations SET title=?, updated_at=? WHERE id=?", (title, now, cid))
            c.execute("DELETE FROM messages WHERE conv_id=?", (cid,))
        else:
            c.execute("INSERT INTO conversations(id,client,title,created_at,updated_at) VALUES(?,?,?,?,?)",
                      (cid, req.client, title, now, now))
        for i, m in enumerate(req.messages):
            c.execute("INSERT INTO messages(conv_id,idx,role,content,entity,grounded,ts) VALUES(?,?,?,?,?,?,?)",
                      (cid, i, m.role, m.content, m.entity, 1 if m.grounded else 0, now))
        c.commit()
    return {"id": cid, "title": title}

@app.delete("/conversations/{cid}")
def del_conv(cid: str):
    with closing(_conn()) as c:
        c.execute("DELETE FROM messages WHERE conv_id=?", (cid,))
        c.execute("DELETE FROM conversations WHERE id=?", (cid,))
        c.commit()
    return {"deleted": cid}

@app.post("/feedback")
def feedback(req: FeedbackReq):
    with closing(_conn()) as c:
        c.execute("""INSERT INTO feedback(conv_id,msg_idx,vote,note,question,answer,entity,ts)
                     VALUES(?,?,?,?,?,?,?,?)""",
                  (req.conv_id, req.msg_idx, req.vote, req.note, req.question, req.answer, req.entity, time.time()))
        c.commit()
    return {"ok": True}

# -------- session memory endpoints (no-op unless MEMORY_ENABLED) --------
class NoteReq(BaseModel):
    entity: str | None = None
    question: str = ""
    session: int = 1

@app.post("/memory/note")
def memory_note(req: NoteReq):
    if not MEM_OK or not req.entity: return {"stored": False}
    return {"stored": MEM.note_interest(req.entity, req.question, req.session)}

@app.get("/memory/retrieve")
def memory_retrieve(q: str, k: int = 4):
    if not MEM_OK: return {"facts": []}
    return {"facts": MEM.retrieve(q, k)}

if __name__ == "__main__":
    import uvicorn
    print(f"store on 0.0.0.0:{PORT} db={DB} memory={MEM_OK}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
