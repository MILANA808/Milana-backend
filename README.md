# Milana Backend (AKSI)

FastAPI backend for **AKSI Dialogic Intelligence**: EQS (emotional metrics), Ψ fields, dialogic loops.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
OpenAPI docs: `http://127.0.0.1:8000/docs`

## API
- `GET /health` — liveness probe.
- `POST /eqs/score` — compute EQS from text (0..100).
- `POST /psi/state` — toy Ψ snapshot (ω, φ, amplitude).

## Docker
```bash
docker build -t milana-backend .
docker run -p 8000:8000 milana-backend
```

## CI/CD
- **CI**: lint + pytest + smoke-run on PR/branches (`.github/workflows/ci.yml`).
- **Docker Publish**: GHCR `ghcr.io/${OWNER}/milana-backend:latest`.
- **Release**: push tag `v*` → tagged image + `latest`.
- **Preview**: ephemeral run on PR (smoke).

## Deploy (Render)
- `render.yaml` prepared (free plan). Link repo in Render → deploy.

## Roadmap
- Replace EQS toy with AKSI real model.
- Add Ψ evolution + persistence.
- Add metrics dashboard.
