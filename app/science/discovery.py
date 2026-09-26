"""AKSI Scientific Discovery Engine — hypothesis-space surgery.

Core primitive:
  1. maintain competing hypotheses;
  2. enumerate executable experiments;
  3. score experiments by expected hypothesis partition / cost;
  4. execute one experiment;
  5. update evidence without inventing unobserved facts.

This is a research prototype, not a claim of scientific novelty.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple
import hashlib, json, math

def canonical(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def digest(x: Any) -> str:
    return hashlib.sha256(canonical(x).encode()).hexdigest()

@dataclass(frozen=True)
class Hypothesis:
    id: str
    description: str
    predictor: Callable[[Any], Any] = field(compare=False, repr=False)
    prior: float = 1.0

@dataclass(frozen=True)
class Experiment:
    id: str
    input: Any
    cost: float = 1.0

@dataclass(frozen=True)
class Observation:
    experiment_id: str
    input: Any
    output: Any
    hypothesis_predictions: Dict[str, Any]
    survivors: Tuple[str, ...]
    observation_hash: str

class DiscoveryEngine:
    """Select the cheapest experiment that maximally separates hypotheses."""

    version = "AKSI-DE/0.1"

    def __init__(self, hypotheses: Sequence[Hypothesis]):
        if not hypotheses:
            raise ValueError("at least one hypothesis is required")
        self.hypotheses = list(hypotheses)
        self.history: List[Observation] = []
        self.active_ids = [h.id for h in self.hypotheses]

    def _active(self) -> List[Hypothesis]:
        active=set(self.active_ids)
        return [h for h in self.hypotheses if h.id in active]

    @staticmethod
    def _entropy(groups: Iterable[int], total: int) -> float:
        if total <= 0: return 0.0
        e=0.0
        for n in groups:
            if n:
                p=n/total; e-=p*math.log2(p)
        return e

    def score_experiment(self, experiment: Experiment) -> Dict[str, Any]:
        hs=self._active()
        predictions: Dict[str, Any] = {}
        groups: Dict[str, int] = {}
        for h in hs:
            p=h.predictor(experiment.input)
            key=canonical(p)
            predictions[h.id]=p
            groups[key]=groups.get(key,0)+1
        prior_entropy=math.log2(len(hs)) if len(hs)>1 else 0.0
        expected_remaining=sum((n/len(hs))*n for n in groups.values())
        expected_information=prior_entropy-math.log2(max(1,expected_remaining))
        partition_count=len(groups)
        utility=expected_information/max(float(experiment.cost),1e-9)
        return {
            "experiment_id":experiment.id,
            "partition_count":partition_count,
            "groups":groups,
            "expected_information_bits":round(expected_information,9),
            "cost":float(experiment.cost),
            "utility":round(utility,9),
            "predictions":predictions,
        }

    def choose_experiment(self, experiments: Sequence[Experiment]) -> Dict[str, Any]:
        ranked=[self.score_experiment(e) for e in experiments]
        ranked.sort(key=lambda x:(x["utility"],x["expected_information_bits"],x["partition_count"]),reverse=True)
        if not ranked: raise ValueError("no experiments supplied")
        return {"protocol":self.version,"selected":ranked[0],"ranked":ranked}

    def observe(self, experiment: Experiment, output: Any) -> Observation:
        hs=self._active()
        predictions={h.id:h.predictor(experiment.input) for h in hs}
        survivors=tuple(h.id for h in hs if predictions[h.id]==output)
        obs=Observation(experiment.id,experiment.input,output,predictions,survivors,digest({
            "experiment_id":experiment.id,"input":experiment.input,"output":output,
            "predictions":predictions,"survivors":survivors}))
        self.history.append(obs)
        if survivors:
            self.active_ids=list(survivors)
        return obs

    def run(self, experiments: Sequence[Experiment], runner: Callable[[Any],Any]) -> Dict[str,Any]:
        choice=self.choose_experiment(experiments)
        selected_id=choice["selected"]["experiment_id"]
        selected=next(e for e in experiments if e.id==selected_id)
        output=runner(selected.input)
        obs=self.observe(selected,output)
        return {
            "protocol":self.version,
            "selected":choice["selected"],
            "observation": {
                "experiment_id":obs.experiment_id,"input":obs.input,"output":obs.output,
                "hypothesis_predictions":obs.hypothesis_predictions,
                "survivors":list(obs.survivors),"observation_hash":obs.observation_hash,
            },
            "remaining_hypotheses":self.active_ids,
            "history_hash":digest([o.observation_hash for o in self.history]),
            "claim_boundary":"The engine records and tests hypotheses; it does not establish that any surviving hypothesis is true.",
        }
