"""AKSI Core control plane: runtime, live events, approvals."""
from __future__ import annotations
import asyncio, hashlib, json, secrets
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.task_store import get as load_task, save as persist_task
router=APIRouter(prefix="/api/core",tags=["AKSI Core"])
def now(): return datetime.now(timezone.utc).isoformat()
def token_hash(token): return hashlib.sha256(token.encode()).hexdigest()
class ApprovalRequest(BaseModel):
    action:str=Field(min_length=1,max_length=100); reason:str=Field(default="",max_length=1000)
class ApprovalUse(BaseModel): token:str=Field(min_length=16,max_length=200)
@router.get("/runtime")
async def runtime():
    return {"ok":True,"name":"AKSI Core","protocol":"AKSI-VAI/1","architecture":["identity","memory","model","tools","policy","evidence","decision","receipt"],"task_states":["CREATED","PLANNING","RESEARCHING","ANALYZING","VERIFYING","COMPLETED","FAILED","STOPPED","NEEDS_PERMISSION","RECOVERABLE"],"external_actions":"approval_required","chain_of_thought":"not_exposed","timestamp":now()}
@router.get("/tasks/{task_id}/events")
async def events(task_id:str):
    if not load_task(task_id): raise HTTPException(404,"Task not found")
    async def stream():
        sent=0; idle=0
        while idle<30:
            task=load_task(task_id)
            if not task: yield 'event: error\ndata: {"error":"Task not found"}\n\n'; return
            journal=task.get("journal",[])
            while sent<len(journal):
                yield f"id: {sent}\nevent: journal\ndata: {json.dumps(journal[sent],ensure_ascii=False)}\n\n"; sent+=1; idle=0
            if task.get("status") in {"COMPLETED","FAILED","STOPPED","NEEDS_PERMISSION","RECOVERABLE"}:
                yield f"event: state\ndata: {json.dumps({'status':task.get('status')},ensure_ascii=False)}\n\n"; return
            yield ": keepalive\n\n"; idle+=1; await asyncio.sleep(1)
    return StreamingResponse(stream(),media_type="text/event-stream",headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})
@router.post("/tasks/{task_id}/approval")
async def request_approval(task_id:str,body:ApprovalRequest):
    task=load_task(task_id)
    if not task: raise HTTPException(404,"Task not found")
    approval={"id":"approval-"+secrets.token_hex(8),"action":body.action,"reason":body.reason,"status":"PENDING","created_at":now()}
    task.setdefault("approvals",[]).append(approval); task["updated_at"]=now(); persist_task(task)
    return {"ok":True,"approval":approval}
@router.post("/tasks/{task_id}/approval/{approval_id}/grant")
async def grant_approval(task_id:str,approval_id:str):
    task=load_task(task_id)
    if not task: raise HTTPException(404,"Task not found")
    for a in task.get("approvals",[]):
        if a.get("id")==approval_id:
            if a.get("status")!="PENDING": raise HTTPException(409,"Approval is not pending")
            token="aksi-approval-"+secrets.token_urlsafe(24); a.update({"status":"GRANTED","token_hash":token_hash(token),"granted_at":now()}); task["updated_at"]=now(); persist_task(task)
            return {"ok":True,"approval_id":approval_id,"status":"GRANTED","token":token}
    raise HTTPException(404,"Approval not found")
@router.post("/tasks/{task_id}/approval/{approval_id}/revoke")
async def revoke_approval(task_id:str,approval_id:str):
    task=load_task(task_id)
    if not task: raise HTTPException(404,"Task not found")
    for a in task.get("approvals",[]):
        if a.get("id")==approval_id:
            a.update({"status":"REVOKED","token_hash":None,"revoked_at":now()}); task["updated_at"]=now(); persist_task(task); return {"ok":True,"approval_id":approval_id,"status":"REVOKED"}
    raise HTTPException(404,"Approval not found")
@router.get("/tasks/{task_id}/approvals")
async def approvals(task_id:str):
    task=load_task(task_id)
    if not task: raise HTTPException(404,"Task not found")
    return {"ok":True,"approvals":[{k:v for k,v in a.items() if k not in {"token","token_hash"}} for a in task.get("approvals",[])]}
@router.post("/tasks/{task_id}/approval/consume")
async def consume_approval(task_id:str,body:ApprovalUse):
    task=load_task(task_id)
    if not task: raise HTTPException(404,"Task not found")
    for a in task.get("approvals",[]):
        if a.get("token_hash")==token_hash(body.token) and a.get("status")=="GRANTED":
            a.update({"status":"CONSUMED","consumed_at":now(),"token_hash":None}); task["updated_at"]=now(); persist_task(task); return {"ok":True,"approval_id":a["id"],"action":a["action"]}
    raise HTTPException(403,"Invalid, revoked, or already consumed approval token")
