# Milana-backend (AKSI)

⚠ **Proprietary Project — All Rights Reserved © 2025 AKSI Project**\
Unauthorized use or reproduction is strictly prohibited.

Integrated platform combining the Milana web portal, AKSI agent runtime, browser computer-use, provenance, memory and backend services.

## AKSI Infinity Agent

AKSI Infinity is a model-independent agent runtime. A task can be planned, researched on the public web, analyzed, verified and returned as a structured report with an integrity receipt. With explicit permission, the runtime can also use a Playwright browser session for computer-use actions.

### Agent capabilities

- Public web search and page extraction
- Browser navigation, reading, screenshots, clicking and form input
- Task journal and bounded background execution
- Model gateway for analysis
- Evidence and source tracking
- Integrity receipts (`AKSI-VAI/1`)
- Explicit permissions for internet, browser actions, downloads, memory and external actions
- Task-scoped, one-time approvals for UI-mutating browser actions

Browser deployment requires Chromium; the Docker image installs it automatically.


## One-click deploy

<a href="https://render.com/deploy?repo=https://github.com/MILANA808/Milana-backend"><img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render"></a>

После нажатия Render прочитает render.yaml и создаст сервис AKSI. Нужен только аккаунт Render и, если нужен облачный LLM, один API key в Environment. Ключи не попадают в GitHub.

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

- DID: generated from the deployed Ed25519 public key (`did:aksi:ed25519:<sha256(pubkey)[:32]>`); retrieve it from `/aksi/seal/public`
- Contact: **aksilove@internet.ru**

Private signing material is never stored in public source files. Configure secrets through deployment environment/secret storage.

## Main endpoints

- `GET /health`
- `GET /api/identity`
- `POST /api/chat` · `POST /api/aksi/chat`
- `POST /api/agent/tasks`
- `GET /api/agent/tasks/{task_id}`
- `POST /api/agent/browser/sessions`
- `POST /api/core/tasks/{task_id}/approval` · request an action approval
- `POST /api/core/tasks/{task_id}/approval/{approval_id}/grant` · grant exactly one requested action
- `POST /api/world/search`
- `GET /api/codex`
- Admin UI: `/admin-ui/`

## License & Contact

**Proprietary License** — All Rights Reserved © 2025 AKSI Project

**Contact**: aksilove@internet.ru

Report security vulnerabilities to: aksilove@internet.ru
