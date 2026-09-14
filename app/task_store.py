"""Durable SQLite task store for AKSI Infinity."""
from __future__ import annotations
import json, os, sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(os.getenv("AKSI_TASK_DB", "data/aksi_tasks.sqlite3"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
TERMINAL = {"COMPLETED", "FAILED", "STOPPED", "NEEDS_PERMISSION"}

def _conn():
    c=sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory=sqlite3.Row
    return c

def init():
    with _conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_updated ON tasks(updated_at DESC)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")

def save(task: Dict[str, Any]):
    with _conn() as c:
        c.execute("INSERT INTO tasks(id,created_at,updated_at,status,payload) VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at,status=excluded.status,payload=excluded.payload", (task['id'],task['created_at'],task['updated_at'],task['status'],json.dumps(task,ensure_ascii=False)))

def get(task_id: str) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        row=c.execute("SELECT payload FROM tasks WHERE id=?",(task_id,)).fetchone()
    return json.loads(row['payload']) if row else None

def list_recent(limit: int=20) -> List[Dict[str, Any]]:
    with _conn() as c:
        rows=c.execute("SELECT payload FROM tasks ORDER BY updated_at DESC LIMIT ?",(max(1,min(limit,100)),)).fetchall()
    return [json.loads(r['payload']) for r in rows]

def list_active(limit: int=100) -> List[Dict[str, Any]]:
    with _conn() as c:
        rows=c.execute("SELECT payload FROM tasks WHERE status NOT IN ('COMPLETED','FAILED','STOPPED','NEEDS_PERMISSION') ORDER BY updated_at ASC LIMIT ?",(max(1,min(limit,500)),)).fetchall()
    return [json.loads(r['payload']) for r in rows]

def mark_recoverable():
    """Mark interrupted in-flight tasks after a process restart; the worker can resume them explicitly."""
    active=list_active()
    for task in active:
        task["status"]="RECOVERABLE"
        task["updated_at"]=task.get("updated_at")
        task.setdefault("journal",[]).append({"message":"Runtime restarted; task is recoverable and awaits worker resume.","status":"recoverable"})
        save(task)
    return len(active)

def delete(task_id: str):
    with _conn() as c:c.execute("DELETE FROM tasks WHERE id=?",(task_id,))
