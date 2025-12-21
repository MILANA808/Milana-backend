from __future__ import annotations

import inspect
import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel

from .exceptions import HTTPException
from .middleware.cors import CORSMiddleware
from .responses import PlainTextResponse


class Header:
    def __init__(self, default: Any = None):
        self.default = default

    def __call__(self) -> Any:
        return self.default


class Request:
    def __init__(self, body: bytes = b"", json_body: Any = None, headers: Optional[Dict[str, str]] = None):
        self._body = body
        self._json = json_body
        self.headers = headers or {}

    async def json(self) -> Any:
        if self._json is not None:
            return self._json
        if not self._body:
            return None
        return json.loads(self._body.decode("utf-8"))

    async def body(self) -> bytes:
        return self._body


class Route:
    def __init__(self, path: str, method: str, func: Callable):
        self.path = path
        self.method = method
        self.func = func


class FastAPI:
    def __init__(self, title: str = "", version: str = "0.1.0"):
        self.title = title
        self.version = version
        self.routes: List[Route] = []

    def add_middleware(self, middleware_class: Any, **kwargs: Any) -> None:  # pragma: no cover - no-op for stub
        return None

    def _register(self, method: str, path: str, **_kwargs: Any):
        def decorator(func: Callable):
            self.routes.append(Route(path, method.upper(), func))
            return func

        return decorator

    def get(self, path: str, **kwargs: Any):
        return self._register("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any):
        return self._register("POST", path, **kwargs)

    def _find_route(self, method: str, path: str) -> Optional[Route]:
        for r in self.routes:
            if r.method == method and r.path == path:
                return r
        return None


# Test client for stubbed environment
class _Response:
    def __init__(self, status_code: int, json_data: Any = None, text: str = "", headers: Optional[Dict[str, str]] = None):
        self.status_code = status_code
        self._json = json_data
        self.text = text
        self.headers = headers or {}

    def json(self) -> Any:
        return self._json


class TestClient:
    __test__ = False  # чтобы pytest не рассматривал класс как тестовый
    def __init__(self, app: FastAPI):
        self.app = app

    def _build_request(self, method: str, url: str, json_body: Any, headers: Optional[Dict[str, str]]) -> Tuple[str, Dict[str, str], Request, Dict[str, str]]:
        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(url)
        path = parsed.path
        query_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        hdrs = {k.lower(): v for k, v in (headers or {}).items()}
        body_bytes = b""
        if json_body is not None:
            body_bytes = json.dumps(json_body).encode("utf-8")
            hdrs.setdefault("content-type", "application/json")
        request = Request(body=body_bytes, json_body=json_body, headers=hdrs)
        return path, query_params, request, hdrs

    def _call(self, method: str, url: str, json_body: Any = None, headers: Optional[Dict[str, str]] = None) -> _Response:
        path, query_params, request, hdrs = self._build_request(method, url, json_body, headers)
        route = self.app._find_route(method, path)
        if not route:
            return _Response(404, {"detail": "Not Found"})

        func = route.func
        try:
            result = self._invoke(func, request, query_params, hdrs)
            if isinstance(result, PlainTextResponse):
                return _Response(200, text=result.content, headers={"content-type": result.media_type})
            return _Response(200, json_data=result)
        except HTTPException as exc:
            return _Response(exc.status_code, {"detail": exc.detail})

    def _invoke(self, func: Callable, request: Request, query: Dict[str, str], headers: Dict[str, str]) -> Any:
        sig = inspect.signature(func)
        kwargs: Dict[str, Any] = {}
        for name, param in sig.parameters.items():
            ann = param.annotation
            if isinstance(ann, str):
                ann = func.__globals__.get(ann, ann)
            if ann is Request or name == "req":
                kwargs[name] = request
                continue
            if isinstance(param.default, Header):
                kwargs[name] = headers.get("x-api-key") or headers.get("x_api_key") or headers.get("x_api-key") or param.default()
                continue
            if (
                ann.__class__.__name__ == "_GenericAlias"
                and getattr(ann, "__origin__", None) is Optional
                and ann.__args__
                and issubclass(ann.__args__[0], str)
                and name.startswith("x_api_key")
            ):
                kwargs[name] = headers.get("x-api-key") or headers.get("x_api_key") or headers.get("x-api-key")
                continue
            if isinstance(ann, type) and issubclass(ann, BaseModel):
                kwargs[name] = ann(**(request._json or {}))
                continue
            if ann is inspect._empty and param.default is inspect._empty:
                kwargs[name] = None
                continue
            if name in query:
                kwargs[name] = type(param.default)(query[name]) if param.default is not inspect._empty else query[name]
                continue
            kwargs[name] = param.default if param.default is not inspect._empty else None
        return func(**kwargs)

    def get(self, url: str, headers: Optional[Dict[str, str]] = None):
        return self._call("GET", url, headers=headers)

    def post(self, url: str, json: Any = None, headers: Optional[Dict[str, str]] = None):
        return self._call("POST", url, json_body=json, headers=headers)


# Backwards compatibility exports
__all__ = [
    "FastAPI",
    "Request",
    "Header",
    "HTTPException",
    "PlainTextResponse",
    "CORSMiddleware",
    "TestClient",
]
