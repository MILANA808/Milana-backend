# АКСИ — дорожная карта воссоздания (по ТЗ 2026-08)

**Эталон:** этот репозиторий (`MILANA808/Milana-backend`) + публичное лицо `milana808.github.io`.

## Важно: расхождение ТЗ и факта

| В ТЗ | В репозитории сейчас |
|------|----------------------|
| React + TypeScript + routes.ts | Vanilla JS `frontend/`, нет React-приложения |
| PostgreSQL + 15+ таблиц | In-memory + JWT auth в `aksi/auth` |
| Полный social / E2E / admin god-mode | Частично: metrics, proof, logs, AI work, crypto keys |
| `app/core/crypto.py` Ed25519 | Запись ключей API; подписи частично; Phase 1: `app/core/crypto.py` |
| 100+ эндпоинтов routes.ts | `main.py` + `aksi/api.py` (v2 agent, tools, memory) |
| GitHub-агент каждые 3 ч | `.aksi/manifest` + workflows; цикл 3 ч — Phase 2 |

**Вывод:** не переписывать всё с нуля «как в ТЗ». Расширять **реальный** код: `main.py`, `aksi/agent.py`, `aksi/tools/*`, `aksi-globe/`, `frontend/`.

Публичный MATRIX (GitHub Pages): offline-чат, quantum, auth, import Replit — уже на `milana808.github.io`.

## Фазы

### Phase 1 — сейчас (скелет суверенитета)
- [x] Gap analysis (этот файл)
- [x] `app/core/crypto.py` — Ed25519, DID, sign/verify
- [x] Identity endpoints: `/api/identity`, proof, did, hash
- [x] Register/Login (SQLite MVP): `/api/register`, `/api/login`, `/api/auth/user`
- [x] Agent handshake + register stub: `/api/agents/*`
- [x] EQS helper + reputation status stub

### Phase 2 — ядро платформы
- PostgreSQL / SQLAlchemy модели (users, chats, posts, agents)
- Social feed + likes (серверная)
- `aksi_engine` stream + web_access (wiki, crypto, weather)
- Подключить MATRIX frontend к API через `AKSI_API`

### Phase 3 — экосистема
- signed_actions + reputation_chain
- GitHub agent 3h cycle (`GITHUB_TOKEN`)
- E2E messages (клиентское шифрование)
- Admin minimal

### Phase 4 — React-портал (опционально)
- Новый `frontend-react/` **или** эволюция vanilla
- 21 apps как маршруты к существующим демо

## Запуск Phase 1

```bash
cd Milana-backend
pip install -r requirements.txt
# cryptography уже через python-jose[cryptography]
uvicorn main:app --reload --port 8000
# docs: http://localhost:8000/docs
```

На MATRIX: `localStorage.setItem('AKSI_API','http://localhost:8000')`

## Не делать
- Не коммитить `GITHUB_TOKEN`, private keys, `.env`
- Не обещать hardware quantum / полный E2E без реализации
- Не дублировать второй «полный» бэкенд в github.io — канон API = **этот** repo
