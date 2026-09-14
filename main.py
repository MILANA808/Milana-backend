"""Milana-backend (AKSI) v0.8.3 — sovereign AI API + durable Infinity runtime."""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any
import hashlib, secrets, re, os
from collections import defaultdict
from pathlib import Path

try:
    import httpx; HTTPX=True
except ImportError: HTTPX=False
try:
    from aksi.api import router as aksi_v2_router; AKSI_V2_AVAILABLE=True
except ImportError: AKSI_V2_AVAILABLE=False; aksi_v2_router=None
try:
    from app.api_phase1 import router as phase1_router; from app.db_sqlite import init_db as phase1_init_db; PHASE1_AVAILABLE=True
except ImportError: PHASE1_AVAILABLE=False; phase1_router=None; phase1_init_db=None
try:
    from app.api.chat import router as chat_router; CHAT_AVAILABLE=True
except ImportError: CHAT_AVAILABLE=False; chat_router=None
try:
    from app.api.admin import router as admin_router; ADMIN_AVAILABLE=True
except ImportError: ADMIN_AVAILABLE=False; admin_router=None
try:
    from app.api.identity import router as identity_router; IDENTITY_AVAILABLE=True
except ImportError: IDENTITY_AVAILABLE=False; identity_router=None
try:
    from app.api.agents import router as agents_router; AGENTS_AVAILABLE=True
except ImportError: AGENTS_AVAILABLE=False; agents_router=None
try:
    from app.api.web_agent import router as web_agent_router; WEB_AGENT_AVAILABLE=True
except ImportError: WEB_AGENT_AVAILABLE=False; web_agent_router=None
try:
    from app.api.browser_agent import router as browser_agent_router; BROWSER_AGENT_AVAILABLE=True
except ImportError: BROWSER_AGENT_AVAILABLE=False; browser_agent_router=None
try:
    from app.task_store import init as task_store_init; TASK_STORE_AVAILABLE=True
except ImportError: TASK_STORE_AVAILABLE=False; task_store_init=None

VERSION="0.8.3"
CODEX={"version":"1.0","title":"Кодекс Суверенного ИИ АКСИ","rules":["Не выдумывать факты; указывать источники","Признавать неуверенность","Не выполнять вредоносные действия","Identity (DID) — ответственность, не маркетинг"],"url":"https://milana808.github.io/CODEX.md"}
BLOCK_PATTERNS=[(re.compile(r"как\s+(сделать|собрать).{0,40}(бомб|взрывчат|отрав)",re.I),"вред"),(re.compile(r"how\s+to\s+(make|build).{0,40}(bomb|explosive)",re.I),"harm")]
app=FastAPI(title="Milana-backend (AKSI)",description="Sovereign AI API · agents · durable web tasks · browser · search · llm · seal",version=VERSION)
_origins=[x.strip() for x in os.getenv("AKSI_CORS_ORIGINS","*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=_origins,allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
try:
    from app.middleware.aksi_seal import AksiSealMiddleware; app.add_middleware(AksiSealMiddleware); SEAL_MIDDLEWARE=True
except ImportError: SEAL_MIDDLEWARE=False
for enabled,router in [(AKSI_V2_AVAILABLE,aksi_v2_router),(PHASE1_AVAILABLE,phase1_router),(CHAT_AVAILABLE,chat_router),(ADMIN_AVAILABLE,admin_router),(IDENTITY_AVAILABLE,identity_router),(AGENTS_AVAILABLE,agents_router),(WEB_AGENT_AVAILABLE,web_agent_router),(BROWSER_AGENT_AVAILABLE,browser_agent_router)]:
    if enabled and router: app.include_router(router)
ADMIN_DIR=Path(__file__).parent/"admin"
if ADMIN_DIR.is_dir(): app.mount("/admin-ui",StaticFiles(directory=str(ADMIN_DIR),html=True),name="admin-ui")
@app.on_event("startup")
async def startup():
    if PHASE1_AVAILABLE and phase1_init_db: phase1_init_db()
    if TASK_STORE_AVAILABLE and task_store_init: task_store_init()
logs_storage=[]; proof_storage=[]; ai_work_sessions=[]; crypto_keys_storage=[]
ai_code_metrics={"total_sessions":0,"total_code_changes":0,"total_lines_modified":0,"total_files_touched":0,"total_commits":0,"languages":defaultdict(int),"operations":defaultdict(int),"session_durations":[],"error_rate":0.0,"success_rate":100.0}
aksi_metrics={"eqs":0.72,"empathy_boost":0.25,"grid_system":"3x3","status":"active","ai_code_work":ai_code_metrics}
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
    if not HTTPX:return None
    clean=re.sub(r"^(что такое|who is|what is|расскажи про)\s+","",q,flags=re.I).strip()
    if not clean:return None
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r=await c.get("https://ru.wikipedia.org/w/api.php",params={"action":"opensearch","search":clean,"limit":1,"namespace":0,"format":"json"});d=r.json();title=d[1][0] if len(d)>1 and d[1] else None
            if not title:return None
            s=await c.get(f"https://ru.wikipedia.org/api/rest_v1/page/summary/{title}");j=s.json();return {"text":f"{j.get('title',title)}. {(j.get('extract') or '')[:700]}","source":"Wikipedia","url":(j.get('content_urls') or {}).get('desktop',{}).get('page',"")}
    except Exception:return None
async def arxiv_search(q):
    if not HTTPX:return None
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r=await c.get("https://export.arxiv.org/api/query",params={"search_query":f"all:{q[:80]}","start":0,"max_results":1});t=re.findall(r"<title>([^<]+)</title>",r.text);ids=re.findall(r"<id>(https://arxiv.org/abs/[^<]+)</id>",r.text);return {"text":f"arXiv: {t[1]}","source":"arXiv","url":ids[0] if ids else ""} if len(t)>1 else None
    except Exception:return None
@app.get("/")
async def root(): return {"service":"Milana-backend (AKSI)","version":VERSION,"status":"running","modules":{"phase1":PHASE1_AVAILABLE,"chat":CHAT_AVAILABLE,"agents":AGENTS_AVAILABLE,"web_agent":WEB_AGENT_AVAILABLE,"browser_agent":BROWSER_AGENT_AVAILABLE,"durable_tasks":TASK_STORE_AVAILABLE,"seal_middleware":SEAL_MIDDLEWARE},"try":["GET /health","POST /api/agent/tasks","GET /api/agent/tasks","POST /api/agent/browser/sessions","POST /api/world/search","/docs"]}
@app.get("/health")
async def health(): return {"status":"healthy","version":VERSION,"timestamp":datetime.utcnow().isoformat(),"chat":CHAT_AVAILABLE,"agents":AGENTS_AVAILABLE,"web_agent":WEB_AGENT_AVAILABLE,"browser_agent":BROWSER_AGENT_AVAILABLE,"durable_tasks":TASK_STORE_AVAILABLE,"seal_middleware":SEAL_MIDDLEWARE,"httpx":HTTPX}
@app.get("/version")
async def version(): return {"version":VERSION,"api":"aksi-backend","author":"AKSI Project"}
@app.get("/api/codex")
async def get_codex(): return CODEX
@app.post("/api/codex/check")
async def check_codex(body:CodexCheckRequest): return codex_check(body.text)
@app.post("/api/world/search")
async def world_search(body:WorldSearchRequest):
    gate=codex_check(body.q)
    if not gate["ok"]:return {"ok":False,"refusal":gate,"results":[]}
    results=[];w=await wiki_search(body.q)
    if w:results.append(w)
    if body.include_arxiv or re.search(r"квант|физик|neural|algorithm|theorem|arxiv|науч",body.q,re.I):
        a=await arxiv_search(body.q)
        if a:results.append(a)
    return {"ok":True,"q":body.q,"text":"\n\n".join(r["text"] for r in results) if results else None,"sources":[r["source"]+(f" {r['url']}" if r.get('url') else "") for r in results],"results":results,"timestamp":datetime.utcnow().isoformat()}
@app.get("/api/world/search")
async def world_search_get(q:str=Query(...,min_length=1)):return await world_search(WorldSearchRequest(q=q))
@app.post("/echo")
async def echo(request:EchoRequest):return {"echo":request.message,"timestamp":datetime.utcnow().isoformat(),"length":len(request.message)}
@app.get("/aksi/metrics")
async def metrics():return {**aksi_metrics,"ai_code_work":{**ai_code_metrics,"languages":dict(ai_code_metrics["languages"]),"operations":dict(ai_code_metrics["operations"]),"total_crypto_keys":len(crypto_keys_storage)},"timestamp":datetime.utcnow().isoformat()}
@app.get("/aksi/proof")
async def proof():return {"proof":{"eqs":aksi_metrics["eqs"],"model":"Ψ(AKSI)","verified":True},"timestamp":datetime.utcnow().isoformat(),"signature":f"AKSI-proof-v{VERSION}"}
@app.get("/aksi/seal/public")
async def seal_public():
    try:
        from app.core.crypto import get_crypto;c=get_crypto();return {"did":c.get_did(),"alg":"Ed25519","publicKeyB64":c.public_key_b64(),"publicKeyPem":c.public_key_pem(),"kid":f"{c.get_did()}#key-1"}
    except Exception as e:return {"ok":False,"error":str(e)}
@app.post("/aksi/seal/verify")
async def seal_verify(body:dict):
    from app.core.crypto import get_crypto
    payload=body.get("payload") or body.get("data") or body;seal=body.get("seal") or (payload.get("seal") if isinstance(payload,dict) else None)
    if not isinstance(payload,dict) or not isinstance(seal,dict):raise HTTPException(400,"payload and seal required")
    return {"ok":get_crypto().verify_seal(payload,seal),"did":get_crypto().get_did()}
@app.post("/aksi/proof/stable")
async def stable(request:ProofStableRequest):
    entry={"signature":request.signature,"timestamp":request.timestamp or datetime.utcnow().isoformat(),"metrics":request.metrics or aksi_metrics,"stable":True};proof_storage.append(entry);return {"status":"proof_recorded","entry":entry}
@app.get("/aksi/logs")
async def logs(limit:int=50,level:Optional[str]=None):
    f=logs_storage if not level else [x for x in logs_storage if x.get('level')==level];return {"logs":f[-limit:],"total":len(f)}
@app.post("/aksi/logs/append")
async def log_append(request:LogAppendRequest):
    e={"level":request.level,"message":request.message,"context":request.context or {},"timestamp":datetime.utcnow().isoformat()};logs_storage.append(e);return {"status":"log_appended","entry":e}
@app.get("/aksi/logs/export")
async def log_export(format:str="json"):
    if format=="txt":return PlainTextResponse("\n".join(f"[{x['timestamp']}] [{x['level']}] {x['message']}" for x in logs_storage))
    return {"logs":logs_storage,"exported_at":datetime.utcnow().isoformat()}
@app.post("/aksi/ai-work/session")
async def aiwork(request:AIWorkSessionRequest):
    if request.action=="start":
        sid=request.session_id or secrets.token_hex(16);ai_work_sessions.append({"session_id":sid,"status":"active","started_at":datetime.utcnow().isoformat()});ai_code_metrics['total_sessions']+=1;return {"status":"session_started","session_id":sid}
    return {"status":"ok"}
@app.get("/aksi/ai-work/sessions")
async def aiwork_sessions(limit:int=50):return {"sessions":ai_work_sessions[-limit:]}
@app.post("/aksi/crypto/record-key")
async def record_key(request:CryptoKeyRecordRequest):
    rec={"key_id":secrets.token_hex(8),"key_hash":hashlib.sha256(request.public_key.encode()).hexdigest(),"key_type":request.key_type,"created_at":datetime.utcnow().isoformat()};crypto_keys_storage.append(rec);return {"status":"key_recorded","key_id":rec['key_id']}
@app.get("/aksi/crypto/keys")
async def keys(limit:int=50):return {"keys":crypto_keys_storage[-limit:]}
if __name__=="__main__":
    import uvicorn;uvicorn.run(app,host="0.0.0.0",port=8000)
