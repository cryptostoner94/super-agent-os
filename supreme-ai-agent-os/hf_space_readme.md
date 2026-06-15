---
title: Agent Runtime Core
emoji: ⚡
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Agent Runtime Core

Production Super AI Agent OS — FastAPI backend with 11 agents, 6 bounty platform connectors, browser automation fallback, and real-time WebSocket task queue.

**API base:** `https://{your-username}-agent-runtime-core.hf.space`

## Endpoints
- `GET /health` — system status
- `GET /agents` — all registered agents
- `GET /tasks` — task queue
- `POST /tasks` — create a task
- `GET /rewards` — bounty opportunities
- `GET /bounty-platforms` — connector status
