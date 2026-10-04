"""AKSI Discovery API — serializable boundary around the scientific kernel.

The API deliberately separates:
- hypothesis generation (untrusted model output),
- experiment selection (deterministic controller),
- observation (external tool/environment),
- evidence update (deterministic),
- receipt generation.

No endpoint executes arbitrary code supplied by a client.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.science.discovery import DiscoveryEngine, Experiment, Hypothesis

router = APIRouter(prefix="/api/discovery", tags=["AKSI Scientific Discovery"])

PROTOCOL = "AKSI-DISCOVERY/1"


class Prediction(BaseModel):
    experiment_id: str
    value: Any


class HypothesisInput(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1, max_length=2000)
    predictions: List[Prediction] = Field(min_length=1, max_length=100)
    prior: float = Field(default=1.0, gt=0)


class ExperimentInput(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    input: Any
    cost: float = Field(default=1.0, gt=0)


class PlanRequest(BaseModel):
    hypotheses: List[HypothesisInput] = Field(min_length=1, max_length=100)
    experiments: List[ExperimentInput] = Field(min_length=1, max_length=100)


class ObserveRequest(BaseModel):
    hypotheses: List[HypothesisInput] = Field(min_length=1, max_length=100)
    experiment: ExperimentInput
    output: Any


def _predictor(h: HypothesisInput):
    table = {p.experiment_id: p.value for p in h.predictions}
    def predict(experiment_input: Any) -> Any:
        # The engine's predictor receives only the experiment input. The API
        # wrapper resolves by the temporary experiment-id carried in context.
        return experiment_input
    return table


def _engine(req: PlanRequest | ObserveRequest) -> tuple[DiscoveryEngine, Dict[str, Any]]:
    tables = {h.id: _predictor(h) for h in req.hypotheses}
    # Use a JSON-serializable envelope as the experiment input so the kernel
    # remains deterministic while the adapter resolves prediction tables.
    experiments = req.experiments if isinstance(req, PlanRequest) else [req.experiment]

    kernel_hypotheses = []
    for h in req.hypotheses:
        table = tables[h.id]
        def make_predictor(t: Dict[str, Any]):
            def predictor(x: Any) -> Any:
                return t.get(str(x.get("id")), {"__missing_prediction__": True})
            return predictor
        kernel_hypotheses.append(
            Hypothesis(h.id, h.description, make_predictor(table), h.prior)
        )

    kernel_experiments = [
        Experiment(e.id, {"id": e.id, "input": e.input}, e.cost) for e in experiments
    ]
    return DiscoveryEngine(kernel_hypotheses), {
        "experiments": {e.id: e for e in kernel_experiments},
        "inputs": {e.id: e.input for e in experiments},
    }


def _receipt(payload: Any) -> Dict[str, Any]:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "protocol": PROTOCOL,
        "sha256": "sha256:" + hashlib.sha256(canonical.encode()).hexdigest(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": "This receipt proves the integrity of the recorded computation, not the truth of a hypothesis.",
    }


@router.get("/protocol")
async def protocol():
    return {
        "protocol": PROTOCOL,
        "architecture": [
            "model proposes hypotheses",
            "deterministic controller selects experiment",
            "external tool/environment produces observation",
            "controller updates evidence",
            "receipt commits the execution record",
        ],
        "safety": "No arbitrary client-supplied code is executed.",
    }


@router.post("/plan")
async def plan(req: PlanRequest):
    engine, meta = _engine(req)
    # The public API uses experiment ids as the kernel input discriminator.
    ranked = engine.choose_experiment(list(meta["experiments"].values()))
    payload = {
        "protocol": PROTOCOL,
        "selected": ranked["selected"],
        "ranked": ranked["ranked"],
        "hypothesis_count": len(req.hypotheses),
        "experiment_count": len(req.experiments),
    }
    return {"ok": True, **payload, "receipt": _receipt(payload)}


@router.post("/observe")
async def observe(req: ObserveRequest):
    engine, meta = _engine(req)
    exp = meta["experiments"][req.experiment.id]
    # Resolve predictions for the selected experiment directly from the
    # declarative input rather than trusting a model-generated claim.
    predictions = {
        h.id: next((p.value for p in h.predictions if p.experiment_id == exp.id), None)
        for h in req.hypotheses
    }
    survivors = [hid for hid, prediction in predictions.items() if prediction == req.output]
    evidence = {
        "experiment_id": exp.id,
        "input": req.experiment.input,
        "output": req.output,
        "predictions": predictions,
        "survivors": survivors,
        "status": "SUPPORTED_BY_OBSERVATION" if survivors else "NO_SURVIVOR",
    }
    evidence["receipt"] = _receipt(evidence)
    return {"ok": True, "evidence": evidence}


@router.post("/synthetic")
async def synthetic(req: PlanRequest):
    """Deterministic integration test: executes a declared hidden rule.

    This endpoint is intentionally synthetic. It proves the control loop can
    select a discriminating experiment and update evidence without granting
    the model arbitrary execution privileges.
    """
    engine, meta = _engine(req)
    ranked = engine.choose_experiment(list(meta["experiments"].values()))
    selected_id = ranked["selected"]["experiment_id"]

    # For a deterministic benchmark, use the first hypothesis as the hidden
    # environment rule. This is a benchmark harness, not a truth oracle.
    hidden = req.hypotheses[0]
    output = next((p.value for p in hidden.predictions if p.experiment_id == selected_id), None)
    evidence = {
        "selected_experiment": selected_id,
        "hidden_rule": hidden.id,
        "observation": output,
        "survivors": [
            h.id for h in req.hypotheses
            if any(p.experiment_id == selected_id and p.value == output for p in h.predictions)
        ],
    }
    payload = {"protocol": PROTOCOL, "plan": ranked, "evidence": evidence}
    return {"ok": True, **payload, "receipt": _receipt(payload)}
