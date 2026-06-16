# Super Agent OS — Operator Guide

## Quick Deploy (One Command)

```bash
git clone https://github.com/cryptostoner94/super-agent-os.git
cd super-agent-os/super-agent-os
bash MASTER_DEPLOY.sh
```

The deploy script handles all steps: validation → build → start → health checks → Ollama model pull → smoke tests.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker | ≥ 24.x | `docker --version` |
| Docker Compose | v2 plugin | `docker compose version` |
| Git | any | For clone |
| curl | any | For health checks |
| RAM | ≥ 4 GB free | Ollama needs 2–4 GB |
| Disk | ≥ 10 GB free | Model files + images |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in what you need. All are optional — the system starts without any keys (Ollama-only mode).

### LLM Providers (pick at least one)

```env
# Local — free, no key required
OLLAMA_BASE_URL=http://localhost:11434   # auto-set in Docker

# Cloud (fallback chain after Ollama)
XAI_API_KEY=                  # Grok-2
GEMINI_API_KEY=               # Gemini 1.5 Flash
OPENAI_API_KEY=               # GPT-4o-mini
GROQ_API_KEY=                 # Llama-3.3 (generous free tier)
OPENROUTER_API_KEY=           # Any model via OpenRouter

# AWS Bedrock
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-haiku-20241022-v1:0
```

### Optional Services

```env
TELEGRAM_BOT_TOKEN=           # Get from @BotFather on Telegram
REDIS_URL=redis://redis:6379  # Falls back to SQLite if unset
```

---

## Starting Services

```bash
# Start everything (API + Dashboard + Ollama)
docker compose up -d api dashboard ollama

# With Telegram bot
TELEGRAM_BOT_TOKEN=your_token docker compose --profile telegram up -d

# With Redis
docker compose --profile redis up -d

# All services
docker compose --profile telegram --profile redis up -d
```

## Stopping

```bash
docker compose down          # stop containers, keep data
docker compose down -v       # stop + wipe volumes
```

---

## Ollama — Local LLM Setup

```bash
# Pull recommended models (after docker compose up ollama)
docker compose exec ollama ollama pull qwen2.5          # general (4.7 GB)
docker compose exec ollama ollama pull qwen2.5-coder    # coding (4.7 GB)
docker compose exec ollama ollama pull llama3.2         # lightweight (2 GB)
docker compose exec ollama ollama pull phi3             # ultra-light (2.3 GB)

# List installed models
docker compose exec ollama ollama list

# Test inference
curl http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5","prompt":"Hello!","stream":false}'
```

The router auto-detects your best installed model — no configuration needed.

---

## Telegram Bot Setup

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`, follow prompts → receive `BOT_TOKEN`
3. Add to `.env`: `TELEGRAM_BOT_TOKEN=your_token`
4. Start with: `docker compose --profile telegram up -d telegram`
5. Message your bot — it routes commands to the agent system

---

## AWS EC2 Deployment

### From your local machine

```bash
export EC2_HOST=your-ec2-public-ip
export EC2_USER=ubuntu            # or ec2-user for Amazon Linux
export EC2_KEY=~/.ssh/your-key.pem

bash MASTER_DEPLOY.sh --aws
```

### Directly on EC2

```bash
curl -fsSL https://raw.githubusercontent.com/cryptostoner94/super-agent-os/main/super-agent-os/MASTER_DEPLOY.sh -o MASTER_DEPLOY.sh
chmod +x MASTER_DEPLOY.sh
bash MASTER_DEPLOY.sh --local
```

### Required EC2 security group rules

| Port | Protocol | Purpose |
|---|---|---|
| 8000 | TCP | FastAPI (required) |
| 8501 | TCP | Streamlit dashboard (required) |
| 11434 | TCP | Ollama API (optional, internal only recommended) |
| 22 | TCP | SSH |

---

## Live Endpoints

| URL | Description |
|---|---|
| `http://HOST:8000/health` | Health check (JSON) |
| `http://HOST:8000/docs` | Auto-generated API docs (Swagger) |
| `http://HOST:8000/api/status` | Agent + task counts |
| `http://HOST:8000/api/agents` | Agent directory |
| `http://HOST:8000/api/browser/status` | Browser engine status |
| `http://HOST:8000/api/memory` | Memory stats |
| `http://HOST:8000/inception/run` | POST — run Inception pipeline |
| `http://HOST:8000/rewards` | Reward opportunities |
| `http://HOST:8000/bounty/plans` | Bug bounty plans |
| `http://HOST:8000/metrics` | Prometheus metrics |
| `http://HOST:8501` | Streamlit dashboard |

---

## Daily Operations

### Stream logs

```bash
docker compose logs -f api               # API logs
docker compose logs -f dashboard         # Dashboard logs
docker compose logs -f telegram          # Telegram bot logs
docker compose logs -f ollama            # Ollama logs
```

### Health check

```bash
curl http://localhost:8000/health | python3 -m json.tool
curl http://localhost:8000/startup | python3 -m json.tool
```

### Restart a service

```bash
docker compose restart api
docker compose restart dashboard
```

### Update to latest

```bash
git pull origin main
docker compose build --no-cache api dashboard
docker compose up -d api dashboard
```

### Run tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/test_api.py -q
```

---

## Browser Engine

Production-grade multi-engine browser with automatic selection:

| Priority | Engine | Source | Capabilities |
|---|---|---|---|
| 1 | `playwright_system` | `/usr/bin/chromium` (Docker) | Full: click, type, screenshot, JS, sessions, download, upload, multi-tab |
| 2 | `playwright_bundled` | Playwright-managed Chromium | Full |
| 3 | `playwright_remote` | Browserless CDP (`BROWSERLESS_URL`) | Full (remote) |
| 4 | `browser_use` | AI-native Playwright wrapper | Full + natural language |
| 5 | `selenium` | `/usr/bin/chromedriver` (Docker) | Full (no multi-tab) |
| fallback | `httpx_fallback` | HTTP client | Text/links only — `available=False` |

**httpx is NOT a browser engine.** `available=True` only when a real browser is running.

### In Docker (default — always full browser)

`docker compose up` starts Browserless automatically. The API connects to it as remote Chrome.
System Chromium in the API container is also tried first.

```bash
# Browserless is always-on (port 3000)
docker compose up -d browserless

# Check which engine is active
curl http://localhost:8000/api/browser/status | python3 -m json.tool

# Browser operations
curl -s -X POST http://localhost:8000/browser/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}' | python3 -c "import json,sys,base64; d=json.load(sys.stdin); open('/tmp/ss.png','wb').write(base64.b64decode(d['screenshot_b64']))" && echo "saved to /tmp/ss.png"
```

### Remote Chromium (Browserless cloud)

```env
# .env
BROWSERLESS_URL=wss://chrome.browserless.io?token=YOUR_TOKEN
```

### Browser API routes

| Route | Method | Description |
|---|---|---|
| `/api/browser/status` | GET | Engine status, availability, features |
| `/api/browser/open` | POST | Fetch page with JS rendering + screenshot |
| `/api/browser/extract` | POST | Extract text and links |
| `/api/browser/screenshot` | POST | Capture full screenshot (base64 PNG) |
| `/api/browser/plan` | POST | Analyze forms on page |
| `/browser/click` | POST | Navigate + click selector |
| `/browser/type` | POST | Fill input field |
| `/browser/upload` | POST | Upload file to input |
| `/browser/download` | POST | Download file to disk |
| `/browser/cookies` | POST | Get session cookies |
| `/browser/tabs` | POST | Open multiple URLs in parallel |
| `/browser/login` | POST | Login + persist session state |
| `/browser/script` | POST | Execute JavaScript |

---

## Data & Storage

All runtime data lives in `data/` (gitignored):

| Path | Contents |
|---|---|
| `data/state/` | Settings, user profile, agent identity |
| `data/artifacts/` | Generated files (Markdown, HTML, CSV, XLSX) |
| `data/.supreme-os/` | Secrets (auto-generated on first run) |
| `data/supreme_memory.db` | SQLite events, outcomes, conversations |

**First-run secrets** are auto-generated at startup — never committed to Git:
- `session_signing_key.bin`
- `encryption_key.bin`
- `agent_identity.json`

---

## LLM Provider Fallback Chain

```
Ollama (auto-detect best model)
  → XAI Grok-2
  → Gemini 1.5 Flash
  → AWS Bedrock (Claude Haiku)
  → OpenAI GPT-4o-mini
  → Groq Llama-3.3
  → OpenRouter (Llama free tier)
  → [error message with setup instructions]
```

The system starts and runs without any API keys — Ollama provides free local inference.

---

## Troubleshooting

### API won't start

```bash
docker compose logs api | tail -50
# Common: missing Python dep → rebuild:
docker compose build --no-cache api
```

### Ollama model not found

```bash
docker compose exec ollama ollama list
docker compose exec ollama ollama pull qwen2.5
```

### Dashboard not connecting to API

Check `SUPREME_API_URL` env var in dashboard container (default: `http://api:8000`).

### Memory DB locked

```bash
docker compose restart api
```

### Out of disk space (model files)

```bash
docker compose exec ollama ollama rm <model-name>
docker system prune -f
```

---

## Agent System

11 agents are registered at startup:

| Agent | Role |
|---|---|
| Executive | Strategic orchestration |
| Planner | Goal decomposition |
| Research | Web research + synthesis |
| Executor | Code + command execution |
| Browser | Web navigation + scraping |
| Code | Software development |
| Memory | Persistent learning |
| Monitor | System observation |
| Telegram | Messaging interface |
| Reward | Revenue discovery |
| Bug Bounty | Security research (authorized only) |

Agents are accessible via:
- Dashboard chat (select agent dropdown)
- `POST /agent/run {"prompt": "...", "agent_id": "executive"}`
- `POST /inception/run {"prompt": "..."}` (full pipeline)
