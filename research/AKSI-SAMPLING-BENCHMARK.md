# AKSI Semantic Sampling Benchmark v0.1

Status: executable research result. The numbers below were reproduced locally from the committed benchmark logic; they are not a theorem.

## Hypothesis
For a bounded class of agent-like trajectories, adaptive semantic sampling can retain fewer or comparable checkpoints while preserving a lower reconstruction error than uniform sampling.

## Configuration
- 500 synthetic runs
- T = 1000 events per run
- 4 semantic dimensions
- 8–24 state transitions
- uniform baseline = 40 checkpoints
- AKSI-S adaptive threshold = 0.30
- AKSI-S maximum gap = 35 events
- reconstruction = piecewise hold from the last checkpoint

## Reproduced result
The benchmark was executed independently in the working environment from the same algorithm:

| Metric | Uniform | AKSI-S adaptive |
|---|---:|---:|
| Mean checkpoints | 40.000 | 38.320 |
| Mean RMSE | 0.193090 | 0.035328 |
| Median adaptive/uniform error ratio | 1.000000 | 0.180900 |
| Runs with lower RMSE | — | 100.0% |

This is a synthetic result. The adaptive sampler is not constrained to exactly the same number of checkpoints, although its measured mean is slightly below the 40-checkpoint baseline.

## What this proves
It shows that, for this synthetic trajectory family and this calibration, a change-sensitive sampler can preserve the trajectory substantially better than uniformly spaced samples at a similar checkpoint budget.

## What this does not prove
- It does not prove arbitrary AI-agent behavior is band-limited.
- It does not establish a new sampling theorem.
- It does not prove reconstruction of hidden chain-of-thought or private model internals.
- It does not establish uniqueness or patentability.
- It does not replace real-agent evaluation.

## Next decisive experiment
Run the same comparison on real AKSI Infinity executions while retaining a full ground-truth trace in a controlled test mode. Evaluate task-state transitions, evidence lineage, permission boundaries and final-result dependencies.