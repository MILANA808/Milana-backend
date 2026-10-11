"""HTTP API for AKSI's transparent classical virtual cluster."""
from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.virtual_cluster import VirtualGPUCluster

router = APIRouter(tags=["AKSI virtual cluster"])
_cluster = VirtualGPUCluster(workers=4)


class MapSumRequest(BaseModel):
    values: List[float] = Field(min_length=1, max_length=1_000_000)


class TrainDemoRequest(BaseModel):
    samples: int = Field(default=512, ge=32, le=100_000)
    steps: int = Field(default=200, ge=1, le=5000)
    learning_rate: float = Field(default=0.05, gt=0, le=1)


@router.get("/aksi/cluster/status")
async def cluster_status():
    """Return simulator status and clearly disclose that workers are CPU simulations."""
    return _cluster.status()


@router.post("/aksi/cluster/map-sum")
async def cluster_map_sum(body: MapSumRequest):
    try:
        return _cluster.map_sum(body.values)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/aksi/cluster/train-demo")
async def cluster_train_demo(body: TrainDemoRequest):
    """Train a tiny synthetic linear model to validate distributed gradient reduction."""
    try:
        return _cluster.train_linear_demo(
            samples=body.samples, steps=body.steps, learning_rate=body.learning_rate
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
