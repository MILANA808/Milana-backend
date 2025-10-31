# AKSI Dialogic Intelligence (вставка)

Этот PR добавляет минимальный прототип FastAPI в папку `aksi_di/`:
- `/health` — проверка сервиса
- `/eqs` — эмоциональный индекс (демо)
- `/psi` — композиция Ψ (демо)

Запуск локально:
```bash
pip install -r aksi_di/requirements.txt
uvicorn aksi_di.app:app --reload --port 8001
```
