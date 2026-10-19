import pytest
from fastapi import HTTPException

from app.api.route_auth import require_task_owner


def test_task_owner_guard_hides_foreign_and_legacy_tasks():
    require_task_owner({"id": "owned", "owner_id": "user-a"}, "user-a")
    for task in ({"id": "foreign", "owner_id": "user-b"}, {"id": "legacy"}):
        with pytest.raises(HTTPException) as exc:
            require_task_owner(task, "user-a")
        assert exc.value.status_code == 404


def test_task_owner_guard_hides_missing_tasks():
    with pytest.raises(HTTPException) as exc:
        require_task_owner(None, "user-a")
    assert exc.value.status_code == 404
