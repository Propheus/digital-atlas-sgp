# Merlion — Singapore Urban Intelligence App

A React + FastAPI frontend for the **Merlion** orchestrator (`merlion/` package).

- **Backend** (FastAPI): wraps the `merlion` Python package, exposes `/api/ask`, `/api/run`, `/api/use_cases`, `/api/audit`.
- **Frontend** (Next.js 14 + Tailwind): dark teal Propheus theme, query box with example prompts, live intent classification + routing panel, JSON result view.

## Quick start (local dev)

```bash
cd merlion-app

# One-time: install deps
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# Start backend (:18700) + frontend (:18701) together
./run_dev.sh
```

Frontend: <http://localhost:18701> · Backend: <http://localhost:18700>

## Environment

Ensure `merlion/.env` contains:
```
ANTHROPIC_API_KEY=...
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend :18701 (Next.js, Tailwind, Framer Motion)          │
│    QueryBox → /api/ask → IntentPanel + ResultPanel           │
└──────────────────────────┬───────────────────────────────────┘
                           │ fetch("/api/ask")
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  Backend :18700 (FastAPI)                                     │
│    /api/ask → merlion.ask(q)                                  │
│      ↓                                                        │
│    [ IntentParser (rules + Claude Sonnet LLM fallback) ]     │
│      ↓                                                        │
│    [ UseCaseRegistry: use_case → model choreography ]        │
│      ↓                                                        │
│    [ Layer 1 (stub today): model execution on parquets ]     │
└──────────────────────────────────────────────────────────────┘
```

## Deploy (rwm-server pattern)

```bash
# Backend
ssh rwm-server
cd ~/digital-atlas-sgp
screen -dmS merlion-api bash -c \
  "cd merlion-app/backend && uvicorn server:app --host 0.0.0.0 --port 18700"

# Frontend (static build)
cd merlion-app/frontend
npm run build
screen -dmS merlion-ui bash -c "npm start"
# Then route merlion.alchemy-propheus.ai → :18701 via nginx.
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET  | `/`                  | health check |
| GET  | `/api/use_cases`     | list registered use cases + model choices |
| GET  | `/api/audit`         | full routing chain + dataset validation |
| POST | `/api/ask`           | natural-language query (body: `{query, top_n?}`) |
| POST | `/api/run`           | direct use case call (body: `{use_case, params}`) |
