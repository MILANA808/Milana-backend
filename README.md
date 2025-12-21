# Milana-backend (AKSI)

⚠ **Proprietary Project — All Rights Reserved © 2025 Alfiia Bashirova (AKSI Project)**\
Unauthorized use or reproduction is strictly prohibited.

FastAPI backend for AKSI / Milana services.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Environment:
- `AKSI_VERSION` — optional semantic version (default: `0.1.0`).
- `AKSI_CORS_ORIGINS` — comma-separated allowed origins (default: `https://milana808.github.io,http://localhost:3000,http://127.0.0.1:3000`).
- `AKSI_LOG_CAP` — max log entries kept in memory (default: `200`).
- `AKSI_DEMO` — `1` to allow public/demo mode (default), `0` to enforce API key.
- `AKSI_API_KEY` — required when `AKSI_DEMO=0`.
- `AKSI_RATE_LIMIT` — requests per minute for EQS/Ψ endpoints (default: `10` in demo, `120` otherwise).
- Offline mode: в репозитории есть лёгкие заглушки FastAPI/uvicorn/pydantic, поэтому тесты и локальная проверка работают даже без доступа к PyPI (CI пропускает установку, если сеть недоступна).

## Endpoints
- `/` — сводка по сервису
- `GET /health`
- `GET /version`
- `POST /echo`
- `POST /eqs/score`
- `POST /psi/state`
- `GET /aksi/metrics`
- `GET /aksi/proof`
- `POST /aksi/proof/stable`
- `GET /aksi/logs`
- `POST /aksi/logs/append`
- `GET /aksi/logs/export`

## Deploy
- **Render**: use `render.yaml` (Python web service).
- **Fly.io**: deploy with the provided `Dockerfile` + `fly.toml`.
- **Railway**: `railway.json` describes a Docker deployment (port 8000).

## Contact
Licensing & business inquiries: **716elektrik@mail.ru** (Alfiia Bashirova)
