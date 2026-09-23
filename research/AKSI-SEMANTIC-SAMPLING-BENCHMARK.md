# AKSI Semantic Sampling — first falsifiable benchmark

Date: 2026-09-23

## Claim under test

A web/AI-agent execution trace may not need every low-level event to remain reconstructable. If the trace contains long stable regions plus sparse semantic state transitions, an event-triggered sampler can preserve reconstruction fidelity with fewer samples than uniform sampling at the same budget.

This is a research hypothesis, not a claim that a new universal sampling theorem has already been proved.

## Experiment

Synthetic agent state:
- 1,000 time steps
- 4 latent state dimensions
- 8–24 semantic state transitions per run
- small observational jitter
- 500 independent runs

Reconstruction: linear interpolation between retained samples.

Compared:
1. Uniform sampler: exactly 40 samples.
2. Adaptive semantic sampler: retain a sample when the smoothed state delta exceeds threshold 0.4, plus endpoints.

## Result

Across 500 runs:

| Method | Mean samples | Mean RMSE |
|---|---:|---:|
| Uniform, budget 40 | 40.0 | 0.2601 |
| Adaptive, threshold 0.4 | 41.69 | 0.1143 |

The adaptive sampler used approximately the same sample budget and reduced mean reconstruction RMSE by about 56%.

Paired result:
- adaptive error / uniform error median: 0.421
- 5th–95th percentile: 0.165–0.904
- adaptive beat uniform in 97.4% of runs.

## Exact restricted theorem

For a semantic execution trace that is piecewise constant with K state transitions, storing the initial state and the state at each transition is sufficient to reconstruct the complete trace exactly.

If the trace contains T time steps, this requires K+1 retained states rather than T observations, giving a compression factor of T/(K+1).

This statement is elementary but rigorous. It establishes the core mechanism under a restricted model.

## What this does NOT prove

It does not prove that arbitrary AI behavior can be reconstructed from sparse samples. Real agent trajectories can contain hidden state, nondeterministic model outputs, rapidly changing environment state, causal dependencies not visible in observations, and irreversible external actions.

Therefore the next scientific test is to define an agent-state representation, a reconstruction error metric, adversarial traces, and a minimum-sampling bound.

## Proposed AKSI research object

**AKSI Semantic Sampling Rate**

For an execution class C and tolerated reconstruction/verification error epsilon, seek the smallest sampling budget N such that a verifier can reconstruct the required semantic state with error <= epsilon.

The important object is therefore not “logs per second”, but:

**minimum authenticated evidence required to verify an agent run.**

That is the part worth trying to formalize as a new protocol/theory.
