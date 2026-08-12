FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY start.sh .
COPY aksi/ ./aksi/
COPY app/ ./app/
COPY admin/ ./admin/

ENV PYTHONUNBUFFERED=1
ENV AKSI_LOG_LEVEL=INFO

RUN mkdir -p /app/.aksi_keys && chmod +x start.sh || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; p=os.environ.get('PORT','8000'); urllib.request.urlopen(f'http://127.0.0.1:{p}/health')" || exit 1

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
