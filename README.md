# Milana Backend (AKSI)

FastAPI backend for AKSI Dialogic Intelligence: EQS (emotional metrics), Ψ fields, and dialogic loops.

## Endpoints
- `GET /health` — liveness probe.
- `POST /eqs/score` — compute EQS for provided text.
- `POST /psi/state` — update/return Ψ-state snapshot.

## Dev
```bash
uv venv .venv && source .venv/bin/activate  # or python -m venv
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## License
Apache-2.0