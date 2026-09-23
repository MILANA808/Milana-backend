"""AKSI Opportunity Engine.

Turns a real-world commercial goal into an evidence-backed opportunity map.
It is intentionally model-independent: discovery, normalization, explicit scoring,
next actions and a cryptographic receipt can run without an LLM API.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/opportunity", tags=["AKSI Opportunity Engine"])


class OpportunityRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=4000)
    market: str = Field(default="", max_length=300)
    keywords: List[str] = Field(default_factory=list, max_length=20)
    max_queries: int = Field(default=6, ge=1, le=12)
    max_results: int = Field(default=30, ge=1, le=100)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def query_set(body: OpportunityRequest) -> List[str]:
    base = clean(" ".join(x for x in [body.goal, body.market] if x))
    keys = [clean(x) for x in body.keywords if clean(x)]
    queries = [base] + [f"{base} {k}" for k in keys]
    queries += [
        f"{base} купить бизнес",
        f"{base} оптом",
        f"{base} поставщик",
        f"{base} партнер",
    ]
    out = []
    for q in queries:
        if q and q not in out:
            out.append(q)
    return out[: body.max_queries]


async def search(client: httpx.AsyncClient, q: str, limit: int = 10) -> List[Dict[str, str]]:
    r = await client.get(
        "https://html.duckduckgo.com/html/",
        params={"q": q},
        headers={"User-Agent": "AKSI-Opportunity-Engine/1.0"},
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for a in soup.select("a.result__a")[:limit]:
        url = a.get("href")
        title = clean(a.get_text(" ", strip=True))
        if not url or not title:
            continue
        rows.append({"title": title, "url": url})
    return rows


def score(item: Dict[str, str], goal: str, keywords: List[str]) -> Dict[str, Any]:
    text = clean(f"{item.get('title','')} {item.get('snippet','')}").lower()
    terms = [clean(x).lower() for x in keywords if clean(x)]
    matched = [x for x in terms if x in text]
    intent_terms = ("купить", "оптом", "партнер", "поставщик", "business", "wholesale", "buyer")
    intent = sum(1 for x in intent_terms if x in text)
    value = min(100, 20 + len(matched) * 15 + intent * 8)
    return {"score": value, "matched_keywords": matched, "intent_signals": intent}


def receipt(payload: Dict[str, Any]) -> Dict[str, Any]:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    seal = None
    did = None
    try:
        from app.core.crypto import get_crypto
        crypto = get_crypto()
        seal = crypto.sign_message(canonical)
        did = crypto.get_did()
    except Exception:
        pass
    return {
        "protocol": "AKSI-OE/1",
        "result_hash": "sha256:" + digest,
        "signature": seal,
        "did": did,
        "claim_boundary": "integrity of the generated opportunity map; public web results are not independently verified facts",
        "timestamp": now(),
    }


@router.post("/discover")
async def discover(body: OpportunityRequest):
    queries = query_set(body)
    raw: List[Dict[str, str]] = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(12, connect=6), follow_redirects=True) as client:
        for q in queries:
            try:
                for item in await search(client, q, max(5, body.max_results // max(1, len(queries)))):
                    item["query"] = q
                    raw.append(item)
            except Exception as exc:
                raw.append({"query": q, "error": type(exc).__name__, "title": "", "url": ""})

    seen = set()
    opportunities = []
    for item in raw:
        url = item.get("url", "")
        if not url or url in seen:
            continue
        seen.add(url)
        host = urlparse(url).netloc.lower()
        scored = score(item, body.goal, body.keywords)
        opportunities.append({
            "title": item.get("title", ""),
            "url": url,
            "domain": host,
            "query": item.get("query", ""),
            **scored,
            "next_action": "open_and_verify",
        })

    opportunities.sort(key=lambda x: (-x["score"], x["domain"], x["title"]))
    opportunities = opportunities[: body.max_results]
    payload = {
        "goal": body.goal,
        "market": body.market,
        "queries": queries,
        "opportunities": opportunities,
        "summary": {
            "queries_run": len(queries),
            "raw_results": len(raw),
            "unique_opportunities": len(opportunities),
            "domains": len({x["domain"] for x in opportunities}),
        },
    }
    return {"ok": True, "engine": "AKSI Opportunity Engine", "version": "1.0", **payload, "receipt": receipt(payload)}
