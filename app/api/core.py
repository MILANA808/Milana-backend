"""AKSI Core control plane: runtime, live events, approvals."""
from __future__ import annotations
import asyncio, importlib, json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.task_store import get as load_task
from app.approval import request_approval as create_approval, grant_approval as grant_token, revoke_approval as revoke_token, public_approvals, consume_approval
router=APIRouter(prefix="/api/core",tags=["AKSI Core"])
MODULES=["aksi.api","app.api_phase1","app.api.chat","app.api.admin","app.api.identity","app.api.agents","app.api.web_agent","app.api.browser_agent","app.api.core"]
def now(): return datetime.now(timezone.utc).isoformat()
class ApprovalRequest(BaseModel):
    action:str=Field(min_length=1,max_length=100); reason:str=Field(default="",max_length=1000)
class ApprovalUse(BaseModel): token:str=Field(min_length=16,max_length=200)
@router.get("/runtime")
async def runtime():
    worker="unknown"
    try:
        from app.api.web_agent import WORKER_TASK
        worker="running" if WORKER_TASK and not WORKER_TASK.done() else "stopped"
    except Exception: pass
    return {"ok":True,"name":"AKSI Core","protocol":"AKSI-VAI/1","architecture":["identity","memory","model","tools","policy","evidence","decision","receipt"],"task_states":["CREATED","PLANNING","RESEARCHING","ANALYZING","VERIFYING","COMPLETED","FAILED","STOPPED","NEEDS_PERMISSION","RECOVERABLE"],"external_actions":"approval_required","chain_of_thought":"not_exposed","worker":worker,"timestamp":now()}
@router.get("/diagnostics/modules")
async def diagnostics_modules():
    result={}
    for name in MODULES:
        try:
            module=importlib.import_module(name); result[name]={"ok":True,"router":hasattr(module,"router")}
        except Exception as exc: result[name]={"ok":False,"error_type":type(exc).__name__,"error":str(exc)[:500]}
    return {"ok":all(item["ok"] for item in result.values()),"modules":result}
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
    approval=await create_approval(task_id,body.action,body.reason)
    return {"ok":True,"approval":approval}
@router.post("/tasks/{task_id}/approval/{approval_id}/grant")
async def grant_approval(task_id:str,approval_id:str):
    token=await grant_token(task_id,approval_id)
    return {"ok":True,"approval_id":approval_id,"status":"GRANTED","token":token}
@router.post("/tasks/{task_id}/approval/{approval_id}/revoke")
async def revoke_approval(task_id:str,approval_id:str):
    await revoke_token(task_id,approval_id)
    return {"ok":True,"approval_id":approval_id,"status":"REVOKED"}
@router.get("/tasks/{task_id}/approvals")
async def approvals(task_id:str): return {"ok":True,"approvals":public_approvals(task_id)}
@router.post("/tasks/{task_id}/approval/consume")
async def consume_approval_route(task_id:str,body:ApprovalUse):
    approval=await consume_approval(task_id,body.token,"*")
    return {"ok":True,"approval_id":approval["id"],"action":approval["action"]}
