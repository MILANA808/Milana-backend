"""AKSI virtual cluster: a real classical CPU simulator for distributed tensor work.

This does not emulate GPU hardware cycle-for-cycle and cannot provide GPU compute
for free. It implements deterministic shard/replicate operations on NumPy arrays,
worker scheduling, checksums, timing and a tiny trainable linear model so AKSI
can validate orchestration and learning mechanics before attaching real accelerators.
"""
from __future__ import annotations

import hashlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Any

import numpy as np


@dataclass
class Worker:
    worker_id: int
    device: str = "cpu-sim"
    memory_budget_mb: int = 256
    jobs_done: int = 0
    total_seconds: float = 0.0


class VirtualGPUCluster:
    def __init__(self, workers: int = 4, memory_budget_mb: int = 256, seed: int = 42):
        if workers < 1 or workers > 64:
            raise ValueError("workers must be between 1 and 64")
        if memory_budget_mb < 1:
            raise ValueError("memory_budget_mb must be positive")
        self.workers = [Worker(i, memory_budget_mb=memory_budget_mb) for i in range(workers)]
        self.rng = np.random.default_rng(seed)
        self.created_at = time.time()
        self.completed_jobs = 0

    @staticmethod
    def _checksum(array: np.ndarray) -> str:
        return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()[:16]

    def status(self) -> dict[str, Any]:
        return {
            "kind": "classical-cpu-simulation",
            "gpu_hardware_present": False,
            "workers": len(self.workers),
            "completed_jobs": self.completed_jobs,
            "uptime_seconds": round(time.time() - self.created_at, 3),
            "workers_detail": [asdict(w) for w in self.workers],
            "warning": "Simulated workers are not physical GPUs and do not multiply available compute.",
        }

    def map_sum(self, values: list[float]) -> dict[str, Any]:
        """Split an input vector, sum shards concurrently, and verify against serial result."""
        x = np.asarray(values, dtype=np.float64)
        if x.ndim != 1 or not np.all(np.isfinite(x)):
            raise ValueError("values must be a finite one-dimensional list")
        shards = [part for part in np.array_split(x, len(self.workers))]
        def run(item):
            worker, shard = item
            start = time.perf_counter()
            result = float(np.sum(shard, dtype=np.float64))
            elapsed = time.perf_counter() - start
            return worker, result, elapsed, len(shard), self._checksum(shard)
        results = []
        with ThreadPoolExecutor(max_workers=len(self.workers)) as pool:
            futures = [pool.submit(run, (self.workers[i], shards[i])) for i in range(len(shards))]
            for f in as_completed(futures):
                results.append(f.result())
        results.sort(key=lambda r: r[0].worker_id)
        for worker, _, elapsed, _, _ in results:
            worker.jobs_done += 1
            worker.total_seconds += elapsed
        self.completed_jobs += len(results)
        partials = [r[1] for r in results]
        total = float(sum(partials))
        reference = float(np.sum(x, dtype=np.float64))
        return {
            "operation": "map_sum",
            "workers": len(results),
            "items": int(x.size),
            "partial_sums": partials,
            "result": total,
            "reference": reference,
            "verified": bool(np.isclose(total, reference, rtol=1e-12, atol=1e-12)),
            "shards": [{"worker_id": r[0].worker_id, "items": r[3], "seconds": round(r[2], 8), "sha256_16": r[4]} for r in results],
        }

    def train_linear_demo(self, samples: int = 512, steps: int = 200, learning_rate: float = 0.05) -> dict[str, Any]:
        """Train a tiny linear regressor with CPU-simulated data shards and deterministic reduction."""
        if samples < 32 or samples > 100_000:
            raise ValueError("samples must be between 32 and 100000")
        if steps < 1 or steps > 5000:
            raise ValueError("steps must be between 1 and 5000")
        if not 0 < learning_rate <= 1:
            raise ValueError("learning_rate must be in (0, 1]")
        rng = np.random.default_rng(123)
        x = rng.normal(size=(samples, 1))
        y = 2.5 * x[:, 0] - 0.7
        w, b = 0.0, 0.0
        started = time.perf_counter()
        for _ in range(steps):
            x_parts = np.array_split(x, len(self.workers))
            y_parts = np.array_split(y, len(self.workers))
            def grad(pair):
                xx, yy = pair
                pred = w * xx[:, 0] + b
                err = pred - yy
                return np.array([2 * np.mean(err * xx[:, 0]), 2 * np.mean(err)])
            with ThreadPoolExecutor(max_workers=len(self.workers)) as pool:
                grads = list(pool.map(grad, zip(x_parts, y_parts)))
            # Weight by shard length to preserve the global mean even for uneven shards.
            weighted = [g * len(x_parts[i]) / samples for i, g in enumerate(grads)]
            g = np.sum(weighted, axis=0)
            w -= learning_rate * float(g[0])
            b -= learning_rate * float(g[1])
        predictions = w * x[:, 0] + b
        mse = float(np.mean((predictions - y) ** 2))
        self.completed_jobs += steps * len(self.workers)
        return {
            "operation": "linear_regression_training_demo",
            "training_samples": samples,
            "steps": steps,
            "workers": len(self.workers),
            "learned_weight": w,
            "learned_bias": b,
            "target_weight": 2.5,
            "target_bias": -0.7,
            "mse": mse,
            "seconds": round(time.perf_counter() - started, 4),
            "verified_converged": bool(mse < 0.02),
            "warning": "This demonstrates distributed gradient reduction on CPU. It is not LLM training and not GPU acceleration.",
        }
