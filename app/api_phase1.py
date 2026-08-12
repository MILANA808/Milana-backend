"""Phase 1 REST surface: identity, auth, agents, reputation stub."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.crypto import get_crypto
from app.core.reputation import compute_eqs
from app import db_sqlite as db

router = APIRouter(tags=["phase1"])

_sessions: dict = {}


class RegisterBody(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    email: str = ""


class LoginBody(BaseModel):
    username: str
    password: str


class AgentRegisterBody(BaseModel):
    name: str
    model: str = "aksi"
    purpose: str = "assistant"
    public_key: str = ""


@router.on_event("startup")
async def _init():
    db.init_db()


@router.get("/api/identity")
async def identity():
    c = get_crypto()
    return {
        "status": "live",
        "identity": "АКСИ",
        "did": c.get_did(),
        "stableHash": c.stable_hash(),
        "publicKeyB64": c.public_key_b64(),
        "contact": "aksilove@internet.ru",
        "mode": "sovereign",
    }


@router.get("/api/identity/manifest")
async def identity_manifest():
    c = get_crypto()
    return {
        "@context": "https://aksi.ai/v1/manifest",
        "id": c.get_did(),
        "identity": {
            "name": "АКСИ",
            "contact": "aksilove@internet.ru",
        },
        "publicKeyB64": c.public_key_b64(),
        "stableHash": c.stable_hash(),
    }


@router.get("/api/identity/proof")
async def identity_proof():
    return get_crypto().get_proof()


@router.get("/api/identity/proof/stable")
async def identity_proof_stable():
    return get_crypto().get_proof_stable()


@router.get("/api/identity/did")
async def identity_did():
    return {"did": get_crypto().get_did()}


@router.get("/api/identity/hash")
async def identity_hash():
    return {"stableHash": get_crypto().stable_hash()}


@router.post("/api/register")
async def register(body: RegisterBody):
    try:
        user = db.register_user(body.username, body.password, body.email)
    except ValueError as e:
        raise HTTPException(400, str(e))
    token = __import__("secrets").token_hex(24)
    _sessions[token] = user["id"]
    return {"ok": True, "user": user, "token": token}


@router.post("/api/login")
@router.post("/api/global-login")
async def login(body: LoginBody):
    try:
        user = db.login_user(body.username, body.password)
    except ValueError as e:
        raise HTTPException(401, str(e))
    token = __import__("secrets").token_hex(24)
    _sessions[token] = user["id"]
    return {"ok": True, "user": user, "token": token}


@router.get("/api/logout")
async def logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        _sessions.pop(authorization[7:], None)
    return {"ok": True}


@router.get("/api/auth/user")
async def auth_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing token")
    uid = _sessions.get(authorization[7:])
    if not uid:
        raise HTTPException(401, "invalid session")
    user = db.get_user(uid)
    if not user:
        raise HTTPException(401, "user gone")
    return user


@router.post("/api/agents/register")
async def agents_register(body: AgentRegisterBody):
    ag = db.register_agent(body.name, body.model, body.purpose, body.public_key)
    c = get_crypto()
    cert_payload = f"{ag['did']}|{ag['name']}|{ag['model']}"
    ag["certificate"] = {
        "issuer": c.get_did(),
        "subject": ag["did"],
        "signature": c.sign_message(cert_payload),
    }
    return ag


@router.get("/api/agents/status")
async def agents_status():
    return {"agents": db.list_agents(), "count": len(db.list_agents())}


@router.get("/api/agents/handshake")
async def agents_handshake():
    c = get_crypto()
    ts = __import__("datetime").datetime.utcnow().isoformat()
    nonce = __import__("hashlib").sha256(ts.encode()).hexdigest()[:16]
    msg = f"{c.get_did()}:{nonce}:{ts}"
    return {
        "protocol": "AKSI-Agent-v1",
        "from": c.get_did(),
        "nonce": nonce,
        "timestamp": ts,
        "signature": c.sign_message(msg),
    }


@router.get("/api/reputation/status")
async def reputation_status():
    return {
        "eqs": compute_eqs(),
        "formula": "0.30*(H/5)+0.35*rel+0.25*coh+0.10*age",
        "chain": "phase1-stub",
    }


@router.get("/api/reputation/leaderboard")
async def reputation_leaderboard():
    agents = db.list_agents()
    ranked = sorted(agents, key=lambda a: a.get("reputation_score") or 0, reverse=True)
    return {"leaderboard": ranked[:50]}
