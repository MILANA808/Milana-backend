# Milana-backend (AKSI)

Запуск локально:
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Endpoints:
- `/health`
- `POST /eqs` {text}
- `POST /psi` {phi, w}

Render запуск (Dockerfile уже настроен).
