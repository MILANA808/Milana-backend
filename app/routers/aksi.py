"""
AKSI bot-specific endpoints
"""

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import os
import json

router = APIRouter()


class LogEntry(BaseModel):
    """Log entry model"""

    timestamp: str
    level: str
    message: str
    metadata: Optional[dict] = None


class ProofData(BaseModel):
    """Proof data model"""

    name: str
    date: str
    proof: str
    stable: bool = False


class MetricsResponse(BaseModel):
    """Metrics response model"""

    total_requests: int
    total_issues_solved: int
    uptime_seconds: float
    timestamp: str


# In-memory storage (in production, use a proper database)
_metrics = {
    "total_requests": 0,
    "total_issues_solved": 0,
    "start_time": datetime.utcnow(),
}

_logs = []
_proofs = []


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get AKSI bot metrics"""
    _metrics["total_requests"] += 1

    uptime = (datetime.utcnow() - _metrics["start_time"]).total_seconds()

    return MetricsResponse(
        total_requests=_metrics["total_requests"],
        total_issues_solved=_metrics["total_issues_solved"],
        uptime_seconds=uptime,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/proof")
async def get_proof():
    """Get AKSI bot proof data"""
    return {
        "name": "AKSI Bot — first AI dev in the world",
        "author": "@AKSI808, Russia",
        "date": "2025-11-16T02:24:00Z",
        "proof": "ChatGPT Codex Connector + write access",
        "stable_proofs": len([p for p in _proofs if p.get("stable", False)]),
        "total_proofs": len(_proofs),
    }


@router.post("/proof/stable")
async def add_stable_proof(proof: ProofData = Body(...)):
    """Add a stable proof record"""
    proof_dict = proof.dict()
    proof_dict["stable"] = True
    proof_dict["recorded_at"] = datetime.utcnow().isoformat()

    _proofs.append(proof_dict)

    return {
        "status": "success",
        "message": "Stable proof recorded",
        "proof_id": len(_proofs) - 1,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/logs")
async def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None, regex="^(INFO|WARNING|ERROR|DEBUG)$"),
):
    """Get AKSI bot logs"""
    logs = _logs

    # Filter by level if specified
    if level:
        logs = [log for log in logs if log.get("level") == level]

    # Apply limit
    logs = logs[-limit:]

    return {
        "logs": logs,
        "total": len(_logs),
        "filtered": len(logs),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/logs/append")
async def append_log(log: LogEntry = Body(...)):
    """Append a log entry"""
    log_dict = log.dict()
    log_dict["id"] = len(_logs)
    log_dict["recorded_at"] = datetime.utcnow().isoformat()

    _logs.append(log_dict)

    return {
        "status": "success",
        "message": "Log entry appended",
        "log_id": len(_logs) - 1,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/logs/export")
async def export_logs(format: str = Query("json", regex="^(json|txt)$")):
    """Export logs in different formats"""
    if format == "json":
        return {
            "format": "json",
            "logs": _logs,
            "exported_at": datetime.utcnow().isoformat(),
        }
    elif format == "txt":
        lines = []
        for log in _logs:
            lines.append(
                f"[{log['timestamp']}] {log['level']}: {log['message']}"
            )

        return {
            "format": "txt",
            "content": "\n".join(lines),
            "exported_at": datetime.utcnow().isoformat(),
        }

    raise HTTPException(status_code=400, detail="Unsupported format")
