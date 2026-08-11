FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY aksi/ ./aksi/
COPY app/ ./app/

ENV PYTHONUNBUFFERED=1
ENV AKSI_LOG_LEVEL=INFO
ENV AKSI_ADMIN_TOKEN=aksi-admin-dev

RUN mkdir -p /app/chromadb_data /app/.aksi_keys

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=8s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
