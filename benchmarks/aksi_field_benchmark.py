"""Deterministic benchmark for AKSI Dynamic Cognitive Field.

Compares adaptive operator selection with a fixed full operator policy.
This is an engineering benchmark, not a claim of superiority.
"""
from __future__ import annotations
from statistics import mean
from app.core.aksi_field import DynamicField

STREAMS = {
    "stable": [
        "temperature normal",
        "temperature normal",
        "temperature normal",
        "temperature normal",
        "temperature normal",
    ],
    "regime_switch": [
        "load low",
        "load low",
        "load low",
        "load high",
        "load high",
        "load high",
    ],
    "noisy": [
        "sensor alpha",
        "sensor gamma",
        "sensor beta",
        "sensor gamma",
        "sensor alpha",
        "sensor delta",
    ],
}

class FixedField(DynamicField):
    def _select(self, ts, evidence, uncertainty):
        return list(self.GENOME)

def run_case(field_cls, stream):
    f = field_cls()
    snapshots = [f.step(x, external_evidence=1, confidence=0.5) for x in stream]
    return {
        "prediction_error": mean(x["prediction_error"] for x in snapshots),
        "stability": mean(x["stability"] for x in snapshots),
        "operator_count": mean(len(x["active_operators"]) for x in snapshots),
        "max_memory": max(x["memory_size"] for x in snapshots),
        "operator_switches": sum(
            snapshots[i]["active_operators"] != snapshots[i-1]["active_operators"]
            for i in range(1, len(snapshots))
        ),
    }

def benchmark():
    cases = {}
    for name, stream in STREAMS.items():
        cases[name] = {
            "dynamic": run_case(DynamicField, stream),
            "fixed": run_case(FixedField, stream),
        }
    return cases

if __name__ == "__main__":
    import json
    print(json.dumps(benchmark(), ensure_ascii=False, indent=2))
