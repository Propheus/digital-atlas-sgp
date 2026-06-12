"""Session-memory adapter — borrows the memory-observatory SemanticStore+Retriever.

Mirrors the transport-adequacy agent's kb.py pattern. Semantic store ONLY (no
episodic/procedural/reflective — those need LLM consolidation). Stores lightweight
{entity, "user_interest", <question>} facts per turn and retrieves them by the
observatory's bag-of-words scorer. OFF unless MEMORY_ENABLED — toggle = restart.

Env: MEMORY_ENABLED (false) · MEMORY_OBSERVATORY_PATH (/root/memory-observatory)
     MEMORY_DB (/root/plexis_memory.db) · MEMORY_MAX_FACTS (4)
"""
from __future__ import annotations
import os, sys, logging
from pathlib import Path
from typing import Optional

log = logging.getLogger("store.memory")
OBS  = Path(os.environ.get("MEMORY_OBSERVATORY_PATH", "/root/memory-observatory"))
MDB  = os.environ.get("MEMORY_DB", "/root/plexis_memory.db")
ENABLED  = os.environ.get("MEMORY_ENABLED", "false").lower() in ("true", "1", "yes", "on")
MAX_FACTS = int(os.environ.get("MEMORY_MAX_FACTS", "4"))

_mgr: Optional[object] = None
_status = {"enabled": ENABLED, "loaded": False, "facts": 0, "reason": ""}

def _init():
    global _mgr, _status
    if not ENABLED:
        _status = {"enabled": False, "loaded": False, "facts": 0, "reason": "toggled off"}; return
    if _mgr is not None: return
    try:
        if not (OBS / "memory" / "memory_manager.py").exists():
            raise RuntimeError(f"not a memory-observatory checkout at {OBS}")
        if str(OBS) not in sys.path: sys.path.insert(0, str(OBS))
        from memory.memory_manager import MemoryManager  # type: ignore
        _mgr = MemoryManager(db_path=MDB, enabled_stores=["semantic"])
        _status = {"enabled": True, "loaded": True, "facts": _mgr.get_stats().get("semantic_count", 0), "db": MDB}
        log.info("session memory ready: %s", _status)
    except Exception as e:  # noqa: BLE001
        _status = {"enabled": True, "loaded": False, "facts": 0, "reason": f"init failed: {e}"}
        log.warning("session memory disabled: %s", e)
_init()

def is_enabled() -> bool: return _status.get("loaded", False)
def status() -> dict: return dict(_status)

def note_interest(entity: str, question: str, session: int = 1) -> bool:
    """Record that the user asked <question> about <entity> (a cheap cross-session fact)."""
    if not is_enabled() or _mgr is None or not entity: return False
    try:
        _mgr.store_semantic([{
            "entity": entity, "attribute": "user_interest",
            "value": (question or "")[:200], "context": "", "source_session": session, "confidence": 1.0,
        }])
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("note_interest failed: %s", e); return False

def retrieve(query: str, k: int = MAX_FACTS) -> list[dict]:
    if not is_enabled() or _mgr is None: return []
    try:
        ranked = _mgr.retrieve(task_context=query, phase="execution")
    except Exception as e:  # noqa: BLE001
        log.warning("retrieve failed: %s", e); return []
    out = []
    for m in ranked[:k]:
        if m.get("memory_type") != "semantic": continue
        out.append({"entity": m.get("entity", ""), "value": m.get("value", ""),
                    "score": round(float(m.get("score", 0.0)), 3)})
    return out
