# Milana Backend (AKSI) — LIVE

[![CI](https://github.com/MILANA808/Milana-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/MILANA808/Milana-backend/actions/workflows/ci.yml)
[![Docker](https://github.com/MILANA808/Milana-backend/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/MILANA808/Milana-backend/actions/workflows/docker-publish.yml)
[![OpenAPI Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://milana808.github.io/Milana-backend/)
[![GHCR](https://img.shields.io/badge/GHCR-milana--backend-informational)](https://github.com/users/MILANA808/packages)

**Live API (Render):** https://milana-backend.onrender.com \ 
• Health: https://milana-backend.onrender.com/health \ 
• Docs: https://milana-backend.onrender.com/docs

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/MILANA808/Milana-backend&branch=main&file=render.yaml)

## Security
- Optional API key via header `X-API-Key` when env `AKSI_API_KEY` is set.
- Dynamic CORS: set `AKSI_CORS_ORIGINS` env to a comma list (e.g. `https://aksi.ai,https://milana.ai`).
- Rate limit: per IP, default **120 req/min** (env `AKSI_RATE_LIMIT`).

## Local run
```bash
docker run -p 8000:8000 ghcr.io/milana808/milana-backend:latest
# or
git clone https://github.com/MILANA808/Milana-backend && cd Milana-backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
