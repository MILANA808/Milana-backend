#!/usr/bin/env bash
set -e
python -m venv .venv
source .venv/bin/activate
if [ -f requirements.txt ]; then pip install -r requirements.txt; else pip install fastapi uvicorn pydantic; fi
cp -n .env.example .env || true
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
