# AKSI Discovery Runtime

This layer turns the scientific kernel into a safe, serializable runtime boundary.

## Execution contract

`hypotheses → experiment selection → external observation → evidence update → receipt`

The language model is allowed to propose hypotheses, but it is not the authority that decides whether a hypothesis is true. The deterministic controller chooses among declared experiments, while the environment/tool produces the observation.

### Endpoints

- `GET /api/discovery/protocol`
- `POST /api/discovery/plan`
- `POST /api/discovery/observe`
- `POST /api/discovery/synthetic`

The API does **not** execute arbitrary client-supplied Python, shell, browser JavaScript, or other code.

## Why this matters

Current agent systems increasingly need persistent state, evidence tracing, authorization and execution provenance rather than a final answer alone. AKSI treats the execution record as a first-class artifact.

## Claim boundary

This is an engineering architecture and benchmark harness. It is not by itself evidence of AGI, consciousness, scientific novelty, or superiority over other agents.
