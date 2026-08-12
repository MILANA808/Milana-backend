# Milana-backend (AKSI)

⚠ **Proprietary Project — All Rights Reserved © 2025 AKSI Project**\
Unauthorized use or reproduction is strictly prohibited.

Integrated platform combining the Milana web portal, AKSI DevOps AI Connector, and backend services.

## Overview

This repository integrates functionality from multiple AKSI projects:
- **Milana Web Portal** (`frontend/`): Interactive web interface with 21 AI-powered applications
- **AKSI Signing Infrastructure** (`.aksi/`, `.github/workflows/`): Cryptographic signing for releases
- **Backend API Services**: FastAPI endpoints for AKSI/Milana services

## Quick Start

### Backend API Server

```bash
pip install -r requirements.txt
python main.py
# or: uvicorn main:app --reload
# or: ./start.sh
```

Server: http://localhost:8000  
Docs: http://localhost:8000/docs

### Docker
```bash
docker-compose up -d
```

## Identity

- DID: `did:aksi:ed25519:sovereign-2026`
- Seed: `AKSI_DIMAX_v3_2026`
- Contact: **aksilove@internet.ru**

## Main endpoints

- `GET /health`
- `GET /api/identity`
- `POST /api/chat` · `POST /api/aksi/chat`
- `POST /api/world/search`
- `GET /api/codex`
- Admin UI: `/admin-ui/`

## License & Contact

**Proprietary License** — All Rights Reserved © 2025 AKSI Project

**Contact**: aksilove@internet.ru

Report security vulnerabilities to: aksilove@internet.ru
