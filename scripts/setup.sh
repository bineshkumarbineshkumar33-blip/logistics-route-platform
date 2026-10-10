#!/usr/bin/env bash
# One-time setup for macOS / Linux / Git Bash. Run from the project root.
set -e
echo "== Backend =="
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
cd ../frontend
echo "== Frontend =="
npm install
echo "Setup finished. Next: scripts/run.sh"
