"""In-memory dialogue store by session_id"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from threading import Lock
from typing import Dict, List

_lock = Lock()
_store: Dict[str, List[dict]] = defaultdict(list)
MAX_PER_SESSION = 200


def append(session_id: str, role: str, content: str) -> None:
    sid = session_id or "default"
    with _lock:
        _store[sid].append(
            {
                "role": role,
                "content": content,
                "ts": datetime.utcnow().isoformat(),
            }
        )
        if len(_store[sid]) > MAX_PER_SESSION:
            _store[sid] = _store[sid][-MAX_PER_SESSION:]


def history(session_id: str, limit: int = 40) -> List[dict]:
    sid = session_id or "default"
    with _lock:
        rows = list(_store.get(sid, []))
    return rows[-limit:]


def context_text(session_id: str, limit: int = 20) -> str:
    rows = history(session_id, limit)
    lines = []
    for r in rows:
        prefix = "User" if r["role"] == "user" else "АКСИ"
        lines.append(f"{prefix}: {r['content']}")
    return "\n".join(lines)


def clear(session_id: str) -> None:
    sid = session_id or "default"
    with _lock:
        _store.pop(sid, None)


def stats() -> dict:
    with _lock:
        return {
            "sessions": len(_store),
            "messages": sum(len(v) for v in _store.values()),
        }
