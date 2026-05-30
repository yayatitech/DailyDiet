#!/usr/bin/env bash
# Full local stack: import JSON → init DB → optional servers
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 scripts/import_xlsm.py
cd backend
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install -q -r requirements.txt
python init_db.py
echo "DB ready. Start API: cd backend && uvicorn app.main:app --reload --port 3000"
