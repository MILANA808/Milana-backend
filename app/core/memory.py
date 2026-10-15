"""Durable SQLite dialogue memory for AKSI.

Set AKSI_MEMORY_DB to choose the database path. The default is data/aksi_memory.sqlite3.
SQLite survives Python process restarts; deployment-level durability still depends on
the host providing persistent storage at that path.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Dict, List

DB_PATH = Path(os.getenv("AKSI_MEMORY_DB", "data/aksi_memory.sqlite3"))
MAX_PER_SESSION = 200
_lock = RLock()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init() -> None:
    """Create the memory schema idempotently."""
    with _lock, _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dialogue_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                ts TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_dialogue_memory_session_id "
            "ON dialogue_memory(session_id, id DESC)"
        )


def append(session_id: str, role: str, content: str) -> None:
    sid = session_id or "default"
    init()
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO dialogue_memory(session_id, role, content, ts) VALUES (?, ?, ?, ?)",
            (sid, role, content, datetime.now(timezone.utc).isoformat()),
        )
        # Keep the same bounded-history contract as the former in-memory store.
        conn.execute(
            """
            DELETE FROM dialogue_memory
            WHERE session_id = ? AND id NOT IN (
                SELECT id FROM dialogue_memory
                WHERE session_id = ? ORDER BY id DESC LIMIT ?
            )
            """,
            (sid, sid, MAX_PER_SESSION),
        )


def history(session_id: str, limit: int = 40) -> List[dict]:
    sid = session_id or "default"
    init()
    safe_limit = max(0, min(int(limit), MAX_PER_SESSION))
    if safe_limit == 0:
        return []
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT role, content, ts FROM ("
            "SELECT id, role, content, ts FROM dialogue_memory "
            "WHERE session_id = ? ORDER BY id DESC LIMIT ?"
            ") ORDER BY id ASC",
            (sid, safe_limit),
        ).fetchall()
    return [dict(row) for row in rows]


def context_text(session_id: str, limit: int = 20) -> str:
    rows = history(session_id, limit)
    lines = []
    for row in rows:
        prefix = "User" if row["role"] == "user" else "АКСИ"
        lines.append(f"{prefix}: {row['content']}")
    return "\n".join(lines)


def clear(session_id: str) -> None:
    sid = session_id or "default"
    init()
    with _lock, _connect() as conn:
        conn.execute("DELETE FROM dialogue_memory WHERE session_id = ?", (sid,))


def stats() -> dict:
    init()
    with _lock, _connect() as conn:
        sessions = conn.execute(
            "SELECT COUNT(DISTINCT session_id) FROM dialogue_memory"
        ).fetchone()[0]
        messages = conn.execute(
            "SELECT COUNT(*) FROM dialogue_memory"
        ).fetchone()[0]
    return {"sessions": sessions, "messages": messages}


init()
