"""AKSI Internet Retrieval Gateway.

Evidence-first public-web retrieval. This is intentionally *not* an unrestricted
network proxy: only public HTTP(S) targets are allowed, redirects are rechecked,
response bytes are streamed with a hard cap, and returned documents are
hash-addressed and marked unverified.
"""
from __future__ import annotations

import asyncio
import hashlib
import html
import ipaddress
import os
import re
import socket
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, HttpUrl

router = APIRouter(prefix="/api/internet", tags=["internet"])

MAX_BYTES = int(os.getenv("AKSI_WEB_MAX_BYTES", "1500000"))
MAX_TEXT = int(os.getenv("AKSI_WEB_MAX_TEXT", "80000"))
TIMEOUT = httpx.Timeout(12.0, connect=5.0)
USER_AGENT = "AKSI-Internet-Gateway/1.1 (+evidence-first retrieval)"
MAX_REDIRECTS = 4
MAX_CONCURRENT_FETCHES = int(os.getenv("AKSI_WEB_MAX_CONCURRENCY", "4"))
RATE_LIMIT = int(os.getenv("AKSI_WEB_RATE_LIMIT", "30"))
RATE_WINDOW = 60.0
_FETCH_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)
_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_RATE_LOCK = asyncio.Lock()


def _public_host(host: str) -> bool:
    """True only when every resolved address is globally routable."""
    host = (host or "").strip().lower().rstrip(".")
    if not host or host in {"localhost", "localhost.localdomain"}:
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError:
        return False
    addresses = {item[4][0] for item in infos}
    if not addresses:
        return False
    return all(_address_is_global(a) for a in addresses)


def _address_is_global(address: str) -> bool:
    try:
        return ipaddress.ip_address(address).is_global
    except ValueError:
        return False


def _validate_url(url: str) -> str:
    p = urlparse(url)
    if p.scheme not in {"http", "https"} or not p.hostname:
        raise HTTPException(400, "Only public http(s) URLs are allowed")
    if p.username or p.password:
        raise HTTPException(400, "Credentials in URLs are not allowed")
    if not _public_host(p.hostname):
        raise HTTPException(403, "Target host is not a public Internet address")
    return url


async def _rate_limit(client_id: str) -> None:
    now = time.monotonic()
    async with _RATE_LOCK:
        bucket = _RATE_BUCKETS[client_id]
        while bucket and now - bucket[0] > RATE_WINDOW:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT:
            raise HTTPException(429, "Internet gateway rate limit exceeded")
        bucket.append(now)


def _clean_text(raw: str) -> str:
    raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.I)
    raw = re.sub(r"<noscript[\s\S]*?</noscript>", " ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw[:MAX_TEXT]


def _evidence(url: str, title: str, text: str, content_type: str, provider: str) -> dict[str, Any]:
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
    return {
        "source_id": f"sha256:{digest}",
        "url": url,
        "title": title[:500],
        "provider": provider,
        "source_type": "web",
        "content_type": content_type,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "content_sha256": digest,
        "text": text,
        "trust": "unverified",
    }


async def _fetch(url: str, provider: str = "direct") -> dict[str, Any]:
    current = _validate_url(url)
    async with _FETCH_SEMAPHORE:
        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain,application/json,application/xml;q=0.9,*/*;q=0.1"},
            follow_redirects=False,
            trust_env=False,
        ) as client:
            for _ in range(MAX_REDIRECTS + 1):
                current = _validate_url(current)
                try:
                    async with client.stream("GET", current) as r:
                        if r.status_code in {301, 302, 303, 307, 308}:
                            location = r.headers.get("location")
                            if not location:
                                break
                            current = urljoin(current, location)
                            continue
                        if r.status_code >= 400:
                            raise HTTPException(r.status_code, f"Upstream returned HTTP {r.status_code}")
                        ctype = r.headers.get("content-type", "application/octet-stream").split(";", 1)[0].lower()
                        if not any(x in ctype for x in ("text/", "json", "xml", "javascript")):
                            raise HTTPException(415, f"Unsupported content type: {ctype}")
                        declared = r.headers.get("content-length")
                        if declared and declared.isdigit() and int(declared) > MAX_BYTES:
                            raise HTTPException(413, "Response is larger than the retrieval limit")
                        chunks: list[bytes] = []
                        total = 0
                        async for chunk in r.aiter_bytes():
                            total += len(chunk)
                            if total > MAX_BYTES:
                                raise HTTPException(413, "Response is larger than the retrieval limit")
                            chunks.append(chunk)
                        content = b"".join(chunks)
                        raw = content.decode(r.encoding or "utf-8", errors="replace")
                        title_match = re.search(r"<title[^>]*>(.*?)</title>", raw, flags=re.I | re.S)
                        title = _clean_text(title_match.group(1)) if title_match else current
                        text = _clean_text(raw)
                        return _evidence(current, title, text, ctype, provider)
                except httpx.TooManyRedirects:
                    break
    raise HTTPException(502, "Too many or invalid redirects")


async def _ddg_search(q: str, limit: int) -> list[dict[str, Any]]:
    params = {"q": q, "kl": "wt-wt"}
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers, follow_redirects=True, trust_env=False) as client:
        r = await client.get("https://html.duckduckgo.com/html/", params=params)
        if r.status_code >= 400:
            raise HTTPException(502, "Search provider unavailable")
        body = r.text
    results: list[dict[str, Any]] = []
    for match in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, re.I | re.S):
        url = html.unescape(match.group(1))
        title = _clean_text(match.group(2))
        if "uddg=" in url:
            url = unquote(parse_qs(urlparse(url).query).get("uddg", [url])[0])
        try:
            _validate_url(url)
        except HTTPException:
            continue
        results.append({"title": title, "url": url, "provider": "DuckDuckGo"})
        if len(results) >= limit:
            break
    return results


class SearchRequest(BaseModel):
    q: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=5, ge=1, le=10)
    fetch_results: bool = False


class FetchRequest(BaseModel):
    url: HttpUrl


@router.post("/search")
async def internet_search(body: SearchRequest, authorization: str | None = Header(None), x_forwarded_for: str | None = Header(None)):
    client_id = (x_forwarded_for or authorization or "anonymous").split(",")[0].strip()[:128]
    await _rate_limit(client_id)
    results = await _ddg_search(body.q, body.limit)
    evidence: list[dict[str, Any]] = []
    if body.fetch_results:
        fetched = await asyncio.gather(*(_fetch(x["url"], "DuckDuckGo") for x in results), return_exceptions=True)
        evidence = [item for item in fetched if isinstance(item, dict)]
    return {"ok": True, "query": body.q, "results": results, "evidence": evidence, "retrieved_at": datetime.now(timezone.utc).isoformat()}


@router.post("/fetch")
async def internet_fetch(body: FetchRequest, authorization: str | None = Header(None), x_forwarded_for: str | None = Header(None)):
    client_id = (x_forwarded_for or authorization or "anonymous").split(",")[0].strip()[:128]
    await _rate_limit(client_id)
    return {"ok": True, "evidence": await _fetch(str(body.url))}
