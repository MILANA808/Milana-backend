# АКСИ — дорожная карта

**Канон API:** этот репозиторий · **публичное лицо:** milana808.github.io

## Статус v0.4.0 (2026-08-11)

| Модуль | Статус |
|--------|--------|
| Ed25519 DID / proof | ✅ `app/core/crypto.py` |
| Register / Login (SQLite) | ✅ `/api/register`, `/api/login` |
| Agents handshake / register | ✅ `/api/agents/*` |
| EQS formula | ✅ `app/core/reputation.py` |
| **Chat SSE АКСИ** | ✅ `/api/aksi/chat`, `/api/chat/stream` |
| **Admin API** | ✅ `/api/admin/*` + `X-Admin-Token` |
| Ollama optional | ✅ через `OLLAMA_URL` |
| PostgreSQL full social | Phase 2 |
| React-Admin UI | Phase 2 |
| GitHub agent 3h | Phase 3 |
| E2E messages | Phase 3 |

## Запуск

```bash
git pull
pip install -r requirements.txt
export AKSI_ADMIN_TOKEN=aksi-admin-dev   # смени в проде
uvicorn main:app --reload --port 8000
```

Проверки:

```bash
curl http://localhost:8000/api/identity
curl -X POST http://localhost:8000/api/chat -H 'Content-Type: application/json' \
  -d '{"message":"кто ты"}'
curl http://localhost:8000/api/admin/stats -H 'X-Admin-Token: aksi-admin-dev'
```

MATRIX: `localStorage.setItem('AKSI_API','http://localhost:8000')`

Docker: `docker compose up --build` (копирует `app/` в образ).

## Честно про «Нобелевский уровень»

Юридически значимый DID + репутация + открытый протокол — правильная цель.  
Один ответ не заменяет месяцы инженерии: social, E2E, React-portal, PG.  
Сейчас — **рабочий суверенный контур**, на котором строится остальное.
