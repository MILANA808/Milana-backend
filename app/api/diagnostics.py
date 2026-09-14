"""AKSI runtime diagnostics: make optional-module failures visible instead of silent."""
from __future__ import annotations

import importlib
from fastapi import APIRouter

router = APIRouter(prefix="/api/diagnostics", tags=["AKSI Diagnostics"])

MODULES = [
    "aksi.api",
    "app.api_phase1",
    "app.api.chat",
    "app.api.admin",
    "app.api.identity",
    "app.api.agents",
    "app.api.web_agent",
    "app.api.browser_agent",
    "app.api.core",
]


@router.get("/modules")
async def modules():
    result = {}
    for name in MODULES:
        try:
            module = importlib.import_module(name)
            result[name] = {"ok": True, "router": hasattr(module, "router")}
        except Exception as exc:
            result[name] = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)[:500]}
    return {"ok": all(item["ok"] for item in result.values()), "modules": result}
