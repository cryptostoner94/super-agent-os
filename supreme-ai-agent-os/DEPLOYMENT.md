# Deployment Guide

## Fastest Path: Railway (one-click from GitHub)

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select `supreme-ai-agent-os`
4. Railway auto-detects `railway.json` and `Dockerfile`
5. Add env vars (at minimum, none are required — system runs with defaults)
6. Deploy → get a public URL

Railway free tier: 500 hours/month. Sufficient for demo/staging.

## Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your GitHub repo
4. Render detects `render.yaml` and deploys both backend + frontend

## Local (Docker)

```bash
cp .env.example .env
# Edit .env with your keys
docker compose up --build
```
Services start on:
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- Ollama: http://localhost:11434

## Local (No Docker)

```bash
# Backend
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd frontend/next-app
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Env Vars

See `.env.example` for the full list. Only `SUPREME_DB_DIR` and `SUPREME_WORKSPACE_DIR` are required (both default to `./data`).

Cloud LLM (optional — system works without):
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY`, `GROQ_API_KEY`

Browser automation (auto-configured in Docker):
- System Chromium used automatically
- `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium` (set in Dockerfile)

## Health Checks

```bash
curl https://your-deploy-url/health
curl https://your-deploy-url/ready
curl https://your-deploy-url/startup   # detailed diagnostics
```
