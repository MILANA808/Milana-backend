FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for quantum libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY aksi/ ./aksi/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV AKSI_LOG_LEVEL=INFO

# Optional: Set API keys via environment variables
# ENV AKSI_OPENAI_API_KEY=your_key
# ENV AKSI_TAVILY_API_KEY=your_key
# ENV AKSI_SERPER_API_KEY=your_key
# ENV AKSI_JWT_SECRET_KEY=your_secret

# Create directory for ChromaDB persistence
RUN mkdir -p /app/chromadb_data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
