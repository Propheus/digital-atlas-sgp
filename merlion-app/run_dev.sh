#!/bin/bash
# Start Merlion backend + frontend in parallel for local dev.
set -e
cd "$(dirname "$0")"

kill_on_exit() { trap 'kill 0' EXIT INT TERM; }
kill_on_exit

echo "[merlion] starting backend on :18700 …"
(cd backend && uvicorn server:app --host 0.0.0.0 --port 18700 --reload) &

sleep 2

echo "[merlion] starting frontend on :18701 …"
(cd frontend && npm run dev) &

wait
