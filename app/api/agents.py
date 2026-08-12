"""API for AKSI multi-agent swarm"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.agents import list_agents, run_agent, run_swarm

router = APIRouter(tags=["agents"])


class AgentRunBody(BaseModel):
    agent: str = Field(..., description="research|analyst|coder|guardian|resonator")
    task: str
    context: Optional[str] = None


class SwarmBody(BaseModel):
    task: str
    context: Optional[str] = None


@router.get("/api/agents")
async def agents_list():
    return {"agents": list_agents(), "swarm": "POST /api/agents/swarm"}


@router.post("/api/agents/run")
async def agents_run(body: AgentRunBody):
    return await run_agent(body.agent, body.task, body.context)


@router.post("/api/agents/swarm")
async def agents_swarm(body: SwarmBody):
    return await run_swarm(body.task, body.context)
