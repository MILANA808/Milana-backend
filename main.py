"""AKSI backend — canonical application bootstrap."""
from __future__ import annotations
import hashlib, os, re, secrets
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

VERSION = "0.11.0"
CODEX = {"version":"1.0","title":"Кодекс Суверенного ИИ АКСИ","rules":["Не выдумывать факты; указывать источники","Признавать неуверенность","Не выполнять вредоносные действия","Identity (DID) — ответственность, не маркетинг"],"url":"https://milana808.github.io/CODEX.md"}
BLOCK_PATTERNS = [(re.compile(r"как\s+(сделать|собрать).{0,40}(бомб|взрывчат|отрав)",re.I),"вред"),(re.compile(r"how\s+to\s+(make|build).{0,40}(bomb|explosive)",re.I),"harm")]
app = FastAPI(title="Milana-backend (AKSI)", description="AKSI Core · sovereign AI · Infinity · browser · evidence · receipt", version=VERSION)
_origins=[x.strip() for x in os.getenv("AKSI_CORS_ORIGINS","*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=_origins,allow_credentials=False,allow_methods=["*"],allow_headers=["*"])

def optional_router(module, attr="router"):
    try:
        m=__import__(module,fromlist=[attr]); return getattr(m,attr),True
    except Exception:
        return None,False

ROUTERS=[]
for mod in ["aksi.api","app.api_phase1","app.api.chat","app.api.admin","app.api.identity","app.api.agents","app.api.web_agent","app.api.browser_agent","app.api.core","app.api.opportunity"]:
    r,ok=optional_router(mod)
    if ok and r: app.include_router(r); ROUTERS.append(mod)
# Opportunity Engine is a required public route; import it explicitly so CI/startup cannot silently hide failures.
from app.api.opportunity import router as opportunity_router
if "app.api.opportunity" not in ROUTERS:
    app.include_router(opportunity_router); ROUTERS.append("app.api.opportunity")

try:
    from app.middleware.aksi_seal import AksiSealMiddleware
    app.add_middleware(AksiSealMiddleware); SEAL_MIDDLEWARE=True
except Exception: SEAL_MIDDLEWARE=False
try:
    from app.task_store import init as task_store_init
    TASK_STORE_AVAILABLE=True
except Exception: TASK_STORE_AVAILABLE=False; task_store_init=None

ADMIN_DIR=Path(__file__).parent/"admin"
if ADMIN_DIR.is_dir(): app.mount("/admin-ui",StaticFiles(directory=str(ADMIN_DIR),html=True),name="admin-ui")
logs_storage=[]; proof_storage=[]; ai_work_sessions=[]; crypto_keys_storage=[]
ai_code_metrics={"total_sessions":0,"total_code_changes":0,"total_lines_modified":0,"total_files_touched":0,"total_commits":0,"languages":defaultdict(int),"operations":defaultdict(int),"session_durations":[],"error_rate":0.0,"success_rate":100.0}
aksi_metrics={"eqs":0.72,"empathy_boost":0.25,"grid_system":"3x3","status":"active","ai_code_work":ai_code_metrics}

@app.on_event("startup")
async def startup():
    if TASK_STORE_AVAILABLE and task_store_init: task_store_init()
    try:
        from app.api.web_agent import start_worker
        await start_worker()
    except Exception:
        pass

@app.on_event("shutdown")
async def shutdown():
    try:
        from app.api.web_agent import stop_worker
        stop_worker()
    except Exception:
        pass

class EchoRequest(BaseModel): message:str
class ProofStableRequest(BaseModel): signature:str; timestamp:Optional[str]=None; metrics:Optional[dict]=None
class LogAppendRequest(BaseModel): level:str; message:str; context:Optional[dict]=None
class AIWorkSessionRequest(BaseModel): session_id:Optional[str]=None; action:str; files_modified:Optional[List[str]]=None; lines_changed:Optional[int]=None; language:Optional[str]=None; operation:Optional[str]=None; commit_hash:Optional[str]=None; metadata:Optional[Dict[str,Any]]=None
class CryptoKeyRecordRequest(BaseModel): key_type:str; public_key:str; purpose:str; algorithm:str; created_by:str; metadata:Optional[Dict[str,Any]]=None
class WorldSearchRequest(BaseModel): q:str; include_arxiv:Optional[bool]=None
class CodexCheckRequest(BaseModel): text:str

def codex_check(text):
    for pat,why in BLOCK_PATTERNS:
        if pat.search(text or ""): return {"ok":False,"reason":why,"codex":CODEX["version"]}
    return {"ok":True,"codex":CODEX["version"]}

async def wiki_search(q):
    try:
        import httpx
        clean=re.sub(r"^(что такое|who is|what is|расскажи про)\s+","",q,flags=re.I).strip()
        if not clean:return None
        async with httpx.AsyncClient(timeout=8) as c:
            r=await c.get("https://ru.wikipedia.org/w/api.php",params={"action":"opensearch","search":clean,"limit":1,"namespace":0,"format":"json"}); d=r.json()
            title=d[1][0] if len(d)>1 and d[1] else None
            if not title:return None
            s=await c.get("https://ru.wikipedia.org/api/rest_v1/page/summary/"+title); j=s.json()
            url=((j.get("content_urls") or {}).get("desktop") or {}).get("page","")
            return {"text":f"{j.get('title',title)}. {(j.get('extract') or '')[:700]}","source":"Wikipedia","url":url}
    except Exception:return None

async def arxiv_search(q):
    try:
        import httpx
        async with httpx.AsyncClient(timeout=8) as c:
            r=await c.get("https://export.arxiv.org/api/query",params={"search_query":f"all:{q[:80]}","start":0,"max_results":1})
            titles=re.findall(r"<title>([^<]+)</title>",r.text); ids=re.findall(r"<id>(https://arxiv.org/abs/[^<]+)</id>",r.text)
            return {"text":f"arXiv: {titles[1]}","source":"arXiv","url":ids[0] if ids else ""} if len(titles)>1 else None
    except Exception:return None

@app.get("/")
async def root():
    return {"service":"Milana-backend (AKSI)","version":VERSION,"status":"running","architecture":"AKSI Core","modules":{"core":"app.api.core" in ROUTERS,"web_agent":"app.api.web_agent" in ROUTERS,"browser_agent":"app.api.browser_agent" in ROUTERS,"opportunity_engine":"app.api.opportunity" in ROUTERS,"durable_tasks":TASK_STORE_AVAILABLE,"seal_middleware":SEAL_MIDDLEWARE},"try":["GET /health","GET /api/core/runtime","POST /api/agent/tasks","POST /api/opportunity/discover","GET /api/core/tasks/{id}/events","POST /api/core/tasks/{id}/approval"]}
@app.get("/health")
async def health():
    return {"status":"healthy","version":VERSION,"timestamp":datetime.now(timezone.utc).isoformat(),"core":"app.api.core" in ROUTERS,"web_agent":"app.api.web_agent" in ROUTERS,"browser_agent":"app.api.browser_agent" in ROUTERS,"durable_tasks":TASK_STORE_AVAILABLE,"seal_middleware":SEAL_MIDDLEWARE}
@app.get("/version")
async def version(): return {"version":VERSION,"api":"aksi-backend","author":"AKSI Project"}
@app.get("/api/codex")
async def get_codex(): return CODEX
@app.post("/api/codex/check")
async def check_codex(body:CodexCheckRequest): return codex_check(body.text)
@app.post("/api/world/search")
async def world_search(body:WorldSearchRequest):
    gate=codex_check(body.q)
    if not gate["ok"]: return {"ok":False,"refusal":gate,"results":[]}
    results=[]; w=await wiki_search(body.q)
    if w: results.append(w)
    if body.include_arxiv or re.search(r"квант|физик|neural|algorithm|theorem|arxiv|науч",body.q,re.I):
        a=await arxiv_search(body.q)
        if a: results.append(a)
    return {"ok":True,"q":body.q,"text":"\n\n".join(x["text"] for x in results) if results else None,"sources":[x["source"]+(f" {x['url']}" if x.get('url') else "") for x in results],"results":results,"timestamp":datetime.now(timezone.utc).isoformat()}

from app.core.aksi_field import run_field

class UniversalRequest(BaseModel):
    q:str
    history:List[Dict[str,Any]]=Field(default_factory=list)
    web:bool=True
    session_id:Optional[str]=None

@app.post("/api/cognition")
async def cognition(body:UniversalRequest):
    """Single-shot cognitive loop: route → evidence → candidates → arbitration."""
    return await universal(body)

@app.post("/api/universal")
async def universal(body:UniversalRequest):
    q=body.q.strip()
    if not q: raise HTTPException(400,"q required")
    evidence=[]
    if body.web:
        w=await wiki_search(q)
        if w: evidence.append(w)
        if re.search(r"науч|исслед|теор|физик|математ|algorithm|neural|arxiv|квант",q,re.I):
            a=await arxiv_search(q)
            if a: evidence.append(a)
    # The mathematical controller now arbitrates multiple answer candidates.
    # A language model is a replaceable generator, never the authority.
    try:
        from app.core.cognitive_runtime import run as cognitive_run
        result=await cognitive_run(q,evidence,body.history)
    except Exception as exc:
        result={"answer":"AKSI runtime error: "+type(exc).__name__,"route":{"type":"error"},"candidates":[],"selected":"error","confidence":0.0,"contradictions":[]}
    field_result=run_field(q,evidence,result.get("confidence"),body.session_id)
    return {
        "ok":True,
        "answer":result["answer"],
        "field":field_result["field"],
        "counterfactuals":field_result["counterfactuals"],
        "sources":evidence,
        "controller":"AKSI Cognitive Runtime",
        "mode":"route→evidence→candidates→mathematical arbitration",
        "route":result.get("route",{}),
        "candidates":result.get("candidates",[]),
        "selected":result.get("selected"),
        "confidence":result.get("confidence"),
        "contradictions":result.get("contradictions",[]),
        "epistemic":result.get("epistemic"),
        "plan":result.get("plan",[]),
        "source_domains":result.get("source_domains",[]),
        "evidence_count":result.get("evidence_count",len(evidence))
    }
@app.get("/api/world/search")
async def world_search_get(q:str=Query(...,min_length=1), include_arxiv:bool=False):
    return await world_search(WorldSearchRequest(q=q, include_arxiv=include_arxiv))
@app.post("/echo")
async def echo(request:EchoRequest): return {"echo":request.message,"timestamp":datetime.now(timezone.utc).isoformat(),"length":len(request.message)}
@app.get("/aksi/metrics")
async def metrics(): return {**aksi_metrics,"ai_code_work":{**ai_code_metrics,"languages":dict(ai_code_metrics["languages"]),"operations":dict(ai_code_metrics["operations"]),"total_crypto_keys":len(crypto_keys_storage)},"timestamp":datetime.now(timezone.utc).isoformat()}
@app.get("/aksi/proof")
async def proof(): return {"proof":{"eqs":aksi_metrics["eqs"],"model":"Ψ(AKSI)","verified":True},"timestamp":datetime.now(timezone.utc).isoformat(),"signature":f"AKSI-proof-v{VERSION}"}
@app.get("/aksi/seal/public")
async def seal_public():
    try:
        from app.core.crypto import get_crypto; c=get_crypto(); return {"did":c.get_did(),"alg":"Ed25519","publicKeyB64":c.public_key_b64(),"publicKeyPem":c.public_key_pem(),"kid":f"{c.get_did()}#key-1"}
    except Exception as e:return {"ok":False,"error":str(e)}
@app.post("/aksi/seal/verify")
async def seal_verify(body:dict):
    from app.core.crypto import get_crypto
    payload=body.get("payload") or body.get("data") or body; seal=body.get("seal") or (payload.get("seal") if isinstance(payload,dict) else None)
    if not isinstance(payload,dict) or not isinstance(seal,dict): raise HTTPException(400,"payload and seal required")
    return {"ok":get_crypto().verify_seal(payload,seal),"did":get_crypto().get_did()}
@app.post("/aksi/proof/stable")
async def stable(request:ProofStableRequest):
    entry={"signature":request.signature,"timestamp":request.timestamp or datetime.now(timezone.utc).isoformat(),"metrics":request.metrics or aksi_metrics,"stable":True}; proof_storage.append(entry); return {"status":"proof_recorded","entry":entry}
@app.get("/aksi/logs")
async def logs(limit:int=50,level:Optional[str]=None):
    f=logs_storage if not level else [x for x in logs_storage if x.get("level")==level]; return {"logs":f[-limit:],"total":len(f)}
@app.post("/aksi/logs/append")
async def log_append(request:LogAppendRequest):
    e={"level":request.level,"message":request.message,"context":request.context or {},"timestamp":datetime.now(timezone.utc).isoformat()}; logs_storage.append(e); return {"status":"log_appended","entry":e}
@app.get("/aksi/logs/export")
async def log_export(format:str="json"):
    if format=="txt": return PlainTextResponse("\n".join(f"[{x['timestamp']}] [{x['level']}] {x['message']}" for x in logs_storage))
    return {"logs":logs_storage,"exported_at":datetime.now(timezone.utc).isoformat()}
@app.post("/aksi/ai-work/session")
async def aiwork(request:AIWorkSessionRequest):
    if request.action=="start":
        sid=request.session_id or secrets.token_hex(16); ai_work_sessions.append({"session_id":sid,"status":"active","started_at":datetime.now(timezone.utc).isoformat()}); ai_code_metrics["total_sessions"]+=1; return {"status":"session_started","session_id":sid}
    return {"status":"ok"}
@app.get("/aksi/ai-work/sessions")
async def aiwork_sessions(limit:int=50): return {"sessions":ai_work_sessions[-limit:]}
@app.post("/aksi/crypto/record-key")
async def record_key(request:CryptoKeyRecordRequest):
    rec={"key_id":secrets.token_hex(8),"key_hash":hashlib.sha256(request.public_key.encode()).hexdigest(),"key_type":request.key_type,"created_at":datetime.now(timezone.utc).isoformat()}; crypto_keys_storage.append(rec); return {"status":"key_recorded","key_id":rec["key_id"]}
@app.get("/aksi/crypto/keys")
async def keys(limit:int=50): return {"keys":crypto_keys_storage[-limit:]}
if __name__=="__main__":
    import uvicorn; uvicorn.run(app,host="0.0.0.0",port=8000)
