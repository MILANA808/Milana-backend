#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=== АКСИ backend ==="
if [ ! -d .venv ]; then
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -r requirements.txt
else
  . .venv/bin/activate
fi

export RESONANCE_SEED="${RESONANCE_SEED:-AKSI_DIMAX_v3_2026}"
export AKSI_DID="${AKSI_DID:-did:aksi:ed25519:sovereign-2026}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-mistral}"

echo "Identity: $AKSI_DID"
echo "Docs: http://127.0.0.1:8000/docs"
echo "Health: http://127.0.0.1:8000/health"
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
