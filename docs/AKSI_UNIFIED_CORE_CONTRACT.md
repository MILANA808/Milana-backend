# AKSI Unified Core — cross-repository contract

**Contract version:** `AKSI-VAI/1`  
**Canonical service:** `MILANA808/Milana-backend`  
**Canonical product client:** `MILANA808/milana808.github.io`

This document defines the integration boundary between the public AKSI site and the FastAPI execution plane. It does not imply the live deployment is reachable; deployment health must be measured.

## Current canonical endpoints

| Purpose | Method/path | Contract notes |
|---|---|---|
| Liveness | `GET /health` | Process-level health only |
| Readiness | `GET /ready` | May return 503 when required capabilities are missing |
| Runtime contract | `GET /api/core/runtime` | Protocol, worker and capability outline |
| Module diagnostics | `GET /api/core/diagnostics/modules` | Import diagnostics; not proof of functional correctness |
| Identity | `GET /api/identity` | Identity and memory stats |
| Chat | `POST /api/chat` | JSON request; returns answer and identity/signature metadata |
| Chat stream | `POST /api/chat/stream` or `/api/aksi/chat` | Server-sent events |
| Create task | `POST /api/agent/tasks` | Goal, explicit permissions, max_sources |
| Read task | `GET /api/agent/tasks/{task_id}` | Current state, result and journal |
| Recent tasks | `GET /api/agent/tasks` | Bounded task listing |
| Task events | `GET /api/core/tasks/{task_id}/events` | SSE journal updates |
| Approval request | `POST /api/core/tasks/{task_id}/approval` | Request a specific action approval |
| Approval grant/revoke | `POST /api/core/tasks/{task_id}/approval/{approval_id}/grant` / `revoke` | Task-scoped; grant must remain explicit |
| Evidence/search capability | See current OpenAPI `/docs` | Do not invent an endpoint if absent |

## Client rules

- The browser client must accept an explicit configured HTTPS base URL; never embed credentials in public JavaScript.
- Only send user text to the backend after a user-triggered action.
- Show backend origin, status, protocol, last successful check and error class without leaking secrets.
- Do not automatically grant internet, browser, download or external-action permissions.
- Treat CORS failure, timeout, HTTP 5xx and missing endpoints as distinct failure states.
- Do not claim that a task succeeded until the task endpoint reports its state.
- Preserve task IDs and the returned journal in the report.
- Avoid automatic retry of task-creation POSTs unless an idempotency key is supported.
- Do not pass private user memory to a model or service without explicit scope and consent.

## Evidence and receipt semantics

- A source URL is a pointer, not proof that the source exists or supports a claim.
- A retrieved source record should contain canonical URL, retrieval time, HTTP status, title, content digest, bounded excerpt and retrieval errors.
- A verifier result must distinguish structural validity, source retrieval, claim support, contradiction and unresolved/untested status.
- SHA-256 protects payload integrity only when the expected digest is preserved independently. It does not establish truth, origin or author identity.
- If a signing key is configured, sign a versioned canonical payload and verify with the published public key. Never return private key material.
- Reports must record contract version, verifier version and code commit.

## Local verification

The repository's `tests/test_runtime.py` exercises health/runtime, task permission gating, single-use approvals and recovery behavior using an isolated SQLite path. Add site-to-backend contract tests against a local FastAPI TestClient or a test server; do not make the core CI depend on a flaky production URL.

## Readiness boundary

`/health` means the process answers. `/ready` should mean only the configured required capabilities are ready. `/api/core/diagnostics/modules` is diagnostic information, not an end-to-end proof. Deployment storage durability, model-provider configuration, CORS and real public reachability require separate live smoke checks.
