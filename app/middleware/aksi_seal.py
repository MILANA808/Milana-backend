"""
AksiSealMiddleware — единый слой подписи АКСИ.

Срабатывает ПОСЛЕ того, как эндпоинт (чат / агент / поиск) сформировал JSON,
и ПЕРЕД отдачей клиенту. В ответ добавляется поле:

  "seal": {
    "did", "alg": "Ed25519", "hash_sha256", "signature", "ts", "kid", "label": "AKSI"
  }
"""
from __future__ import annotations

import json
import logging
from typing import Callable, Iterable, Optional, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("aksi.seal")

DEFAULT_PREFIXES: tuple[str, ...] = (
    "/api/",
    "/aksi/",
    "/echo",
    "/v1/",
    "/v2/",
)

SKIP_EXACT: Set[str] = {
    "/health",
    "/version",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/aksi/seal/public",
}


class AksiSealMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        prefixes: Optional[Iterable[str]] = None,
        skip: Optional[Iterable[str]] = None,
    ):
        super().__init__(app)
        self.prefixes = tuple(prefixes) if prefixes is not None else DEFAULT_PREFIXES
        self.skip = set(skip) if skip is not None else set(SKIP_EXACT)

    def _should_seal(self, path: str) -> bool:
        if path in self.skip:
            return False
        if path.startswith("/admin") or path.startswith("/static"):
            return False
        return any(path == p or path.startswith(p) for p in self.prefixes)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        if request.method == "OPTIONS":
            return response
        if not self._should_seal(request.url.path):
            return response

        ctype = (response.headers.get("content-type") or "").lower()
        if "application/json" not in ctype:
            return response

        body_bytes = b""
        try:
            async for chunk in response.body_iterator:
                body_bytes += chunk if isinstance(chunk, (bytes, bytearray)) else chunk.encode()
        except Exception:
            return response

        if not body_bytes:
            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        try:
            data = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )

        if not isinstance(data, dict):
            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )

        if "seal" in data and isinstance(data.get("seal"), dict) and data["seal"].get("signature"):
            return JSONResponse(content=data, status_code=response.status_code)

        try:
            from app.core.crypto import get_crypto

            crypto = get_crypto()
            data["seal"] = crypto.seal_payload(data)
        except Exception as e:
            logger.warning("aksi seal skipped: %s", e)
            data["seal"] = {
                "alg": "none",
                "note": "signer unavailable",
                "error": type(e).__name__,
            }

        headers = {
            k: v
            for k, v in response.headers.items()
            if k.lower() not in ("content-length", "content-type")
        }
        return JSONResponse(content=data, status_code=response.status_code, headers=headers)
