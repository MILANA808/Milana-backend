import asyncio
import pytest
from fastapi import HTTPException

import app.approval as approval


def test_requester_cannot_grant_own_approval(monkeypatch):
    task = {"id": "task-1", "approvals": []}
    monkeypatch.setattr(approval, "_task", lambda _task_id: task)
    monkeypatch.setattr(approval, "persist_task", lambda _task: None)

    request = asyncio.run(approval.request_approval(
        "task-1", "browser.click", "test action", requester_id="user-a"
    ))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(approval.grant_approval(
            "task-1", request["id"], approver_id="user-a"
        ))
    assert exc.value.status_code == 403

    token = asyncio.run(approval.grant_approval(
        "task-1", request["id"], approver_id="user-b"
    ))
    assert token.startswith("aksi-approval-")
    assert task["approvals"][0]["approver_id"] == "user-b"
