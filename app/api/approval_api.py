"""Approval API for AKSI task-scoped real-world actions."""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.approval import request_approval, grant_approval, revoke_approval, public_approvals

router = APIRouter(prefix="/api/agent", tags=["AKSI Approvals"])

class ApprovalRequest(BaseModel):
    action: str = Field(min_length=3, max_length=120)
    reason: str = Field(default="", max_length=1000)

class ApprovalGrant(BaseModel):
    approval_id: str = Field(min_length=8, max_length=200)

@router.post("/tasks/{task_id}/approvals")
async def create_approval(task_id: str, body: ApprovalRequest):
    approval = await request_approval(task_id, body.action, body.reason)
    return {"ok": True, "approval": approval}

@router.get("/tasks/{task_id}/approvals")
async def list_approvals(task_id: str):
    return {"ok": True, "approvals": public_approvals(task_id)}

@router.post("/tasks/{task_id}/approvals/grant")
async def grant(task_id: str, body: ApprovalGrant):
    token = await grant_approval(task_id, body.approval_id)
    # Token is returned exactly once to the approving client.
    return {"ok": True, "approval_id": body.approval_id, "approval_token": token}

@router.post("/tasks/{task_id}/approvals/{approval_id}/revoke")
async def revoke(task_id: str, approval_id: str):
    await revoke_approval(task_id, approval_id)
    return {"ok": True, "status": "REVOKED"}
