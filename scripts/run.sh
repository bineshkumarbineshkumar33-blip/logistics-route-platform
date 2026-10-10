#!/usr/bin/env bash
# Starts backend (:8000) and frontend (:5173). Ctrl+C stops both.
cd "$(dirname "$0")/.."
( cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000 ) &
BACK=$!
trap "kill $BACK 2>/dev/null" EXIT
cd frontend && npm run dev
