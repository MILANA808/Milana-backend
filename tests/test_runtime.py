import os
import time

# Keep test state isolated from any developer/deployment database.
os.environ["AKSI_TASK_DB"] = "/tmp/aksi-test-tasks.sqlite3"

from fastapi.testclient import TestClient

from app import task_store
from main import app


def wait_for_status(client, task_id, wanted, timeout=5):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        response = client.get(f"/api/agent/tasks/{task_id}")
        assert response.status_code == 200
        last = response.json()["task"]["status"]
        if last in wanted:
            return last
        time.sleep(0.05)
    raise AssertionError(f"status did not reach {wanted}; last={last}")


def test_health_and_core_runtime():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"

        runtime = client.get("/api/core/runtime")
        assert runtime.status_code == 200
        body = runtime.json()
        assert body["protocol"] == "AKSI-VAI/1"
        assert body["external_actions"] == "approval_required"
        assert body["chain_of_thought"] == "not_exposed"


def test_task_persists_and_requires_internet_permission():
    task_store.init()
    with TestClient(app) as client:
        response = client.post(
            "/api/agent/tasks",
            json={
                "goal": "Проверить lifecycle runtime",
                "permissions": {"internet": False, "read_pages": True},
            },
        )
        assert response.status_code == 200
        task_id = response.json()["task"]["id"]

        assert wait_for_status(client, task_id, {"NEEDS_PERMISSION"}) == "NEEDS_PERMISSION"
        persisted = task_store.get(task_id)
        assert persisted is not None
        assert persisted["id"] == task_id
        assert any("требуется разрешение" in x["message"] for x in persisted["journal"])


def test_approval_token_is_single_use():
    task_store.init()
    with TestClient(app) as client:
        response = client.post(
            "/api/agent/tasks",
            json={
                "goal": "Проверить approval lifecycle",
                "permissions": {"internet": False},
            },
        )
        task_id = response.json()["task"]["id"]
        wait_for_status(client, task_id, {"NEEDS_PERMISSION"})

        requested = client.post(
            f"/api/core/tasks/{task_id}/approval",
            json={"action": "browser.interact", "reason": "explicit test approval"},
        )
        assert requested.status_code == 200
        approval_id = requested.json()["approval"]["id"]

        granted = client.post(f"/api/core/tasks/{task_id}/approval/{approval_id}/grant")
        assert granted.status_code == 200
        token = granted.json()["token"]
        assert token

        consumed = client.post(
            f"/api/core/tasks/{task_id}/approval/consume",
            json={"token": token},
        )
        assert consumed.status_code == 200
        assert consumed.json()["action"] == "browser.interact"

        replay = client.post(
            f"/api/core/tasks/{task_id}/approval/consume",
            json={"token": token},
        )
        assert replay.status_code == 403

        approvals = client.get(f"/api/core/tasks/{task_id}/approvals")
        assert approvals.status_code == 200
        assert approvals.json()["approvals"][0]["status"] == "CONSUMED"


def test_recovery_marks_interrupted_task():
    task_store.init()
    task_id = "recovery-test"
    task_store.delete(task_id)
    task_store.save(
        {
            "id": task_id,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "status": "RESEARCHING",
            "stop_requested": False,
            "journal": [],
        }
    )

    recovered = task_store.mark_recoverable()
    assert any(t["id"] == task_id for t in recovered)
    task = task_store.get(task_id)
    assert task["status"] == "RECOVERABLE"
    assert task["stop_requested"] is False
    assert task["journal"][-1]["status"] == "recoverable"
