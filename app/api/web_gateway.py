"""AKSI Internet Retrieval Gateway.

Server-side, keyless retrieval for arbitrary public web pages plus search.
The gateway is deliberately evidence-first: every fetched document gets a
content SHA-256, retrieval timestamp, source URL and bounded text payload.
It blocks localhost/private/link-local targets to reduce SSRF risk and only
supports HTTP(S). This is retrieval, not an LLM or truth oracle.
"""

from __future__ import annotations

import asyncio
import hashlib
import html
import ipaddress
import re
import socket
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl

router = APIRouter(prefix="/api/internet", tags=["internet"])

MAX_BYTES = 1_500_000
MAX_TEXT = 80_000
TIMEOUT = httpx.Timeout(12.0, connect=5.0)
USER_AGENT = "AKSI-Internet-Gateway/1.0 (+evidence-first retrieval)"


def _public_host(host: str) -> bool:
    """Return True only for DNS/IP targets that are not private/reserved."""
    host = (host or "").strip().lower().rstrip(".")
    if not host or host in {"localhost", "localhost.localdomain"}:
        return False
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_global
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError:
        return False
    addresses = {item[4][0] for item in infos}
    if not addresses:
        return False
    for address in addresses:
        try:
            if not ipaddress.ip_address(address).is_global:
                return False
        except ValueError:
            return False
    return True


def _validate_url(url: str) -> str:
    p = urlparse(url)
    if p.scheme not in {"http", "https"} or not p.hostname:
        raise HTTPException(400, "Only public http(s) URLs are allowed")
    if p.username or p.password:
        raise HTTPException(400, "Credentials in URLs are not allowed")
    if not _public_host(p.hostname):
        raise HTTPException(403, "Target host is not a public Internet address")
    return url


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
    async with httpx.AsyncClient(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}, follow_redirects=False) as client:
        for _ in range(4):
            r = await client.get(current)
            if r.status_code in {301, 302, 303, 307, 308}:
                location = r.headers.get("location")
                if not location:
                    break
                current = _validate_url(urljoin(current, location))
                continue
            if r.status_code >= 400:
                raise HTTPException(r.status_code, f"Upstream returned HTTP {r.status_code}")
            content = r.content[: MAX_BYTES + 1]
            if len(content) > MAX_BYTES:
                raise HTTPException(413, "Response is larger than the retrieval limit")
            ctype = r.headers.get("content-type", "application/octet-stream").split(";", 1)[0].lower()
            if not any(x in ctype for x in ("text/", "json", "xml", "javascript")):
                raise HTTPException(415, f"Unsupported content type: {ctype}")
            raw = content.decode(r.encoding or "utf-8", errors="replace")
            title_match = re.search(r"<title[^>]*>(.*?)</title>", raw, flags=re.I | re.S)
            title = _clean_text(title_match.group(1)) if title_match else current
            text = _clean_text(raw)
            return _evidence(current, title, text, ctype, provider)
    raise HTTPException(502, "Too many or invalid redirects")


async def _ddg_search(q: str, limit: int) -> list[dict[str, Any]]:
    params = {"q": q, "kl": "wt-wt"}
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers) as client:
        r = await client.get("https://html.duckduckgo.com/html/", params=params)
        if r.status_code >= 400:
            raise HTTPException(502, "Search provider unavailable")
        body = r.text

    results: list[dict[str, Any]] = []
    for match in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, re.I | re.S):
        url = html.unescape(match.group(1))
        title = _clean_text(match.group(2))
        if "uddg=" in url:
            try:
                from urllib.parse import parse_qs
                url = parse_qs(urlparse(url).query).get("uddg", [url])[0]
            except Exception:
                pass
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
async def internet_search(body: SearchRequest):
    """Search the public web; optionally fetch the returned pages into evidence."""
    results = await _ddg_search(body.q, body.limit)
    evidence: list[dict[str, Any]] = []
    if body.fetch_results:
        fetched = await asyncio.gather(*(_fetch(x["url"], "DuckDuckGo") for x in results), return_exceptions=True)
        for item in fetched:
            if isinstance(item, dict):
                evidence.append(item)
    return {
        "ok": True,
        "query": body.q,
        "results": results,
        "evidence": evidence,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/fetch")
async def internet_fetch(body: FetchRequest):
    """Fetch one public URL and return bounded, hash-addressed evidence."""
    return {"ok": True, "evidence": await _fetch(str(body.url))}
