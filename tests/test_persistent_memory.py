"""Tests for persistent AKSI dialogue memory."""
import importlib
import os


def test_memory_persists_across_module_reload(tmp_path, monkeypatch):
    db_path = tmp_path / "memory.sqlite3"
    monkeypatch.setenv("AKSI_MEMORY_DB", str(db_path))

    import app.core.memory as memory
    memory = importlib.reload(memory)
    memory.clear("session-a")
    memory.append("session-a", "user", "hello")
    memory.append("session-a", "assistant", "world")

    # Reload simulates a Python process/module restart using the same DB file.
    memory = importlib.reload(memory)
    assert memory.history("session-a") == [
        {"role": "user", "content": "hello", "ts": memory.history("session-a")[0]["ts"]},
        {"role": "assistant", "content": "world", "ts": memory.history("session-a")[1]["ts"]},
    ]
    assert memory.context_text("session-a") == "User: hello\nАКСИ: world"


def test_memory_clear_is_session_scoped(tmp_path, monkeypatch):
    monkeypatch.setenv("AKSI_MEMORY_DB", str(tmp_path / "memory.sqlite3"))
    import app.core.memory as memory
    memory = importlib.reload(memory)
    memory.append("one", "user", "keep")
    memory.append("two", "user", "remove")
    memory.clear("two")
    assert [item["content"] for item in memory.history("one")] == ["keep"]
    assert memory.history("two") == []


def test_memory_bounds_history_per_session(tmp_path, monkeypatch):
    monkeypatch.setenv("AKSI_MEMORY_DB", str(tmp_path / "memory.sqlite3"))
    import app.core.memory as memory
    memory = importlib.reload(memory)
    for i in range(memory.MAX_PER_SESSION + 3):
        memory.append("bounded", "user", str(i))
    rows = memory.history("bounded", limit=memory.MAX_PER_SESSION)
    assert len(rows) == memory.MAX_PER_SESSION
    assert rows[0]["content"] == "3"
    assert rows[-1]["content"] == str(memory.MAX_PER_SESSION + 2)
