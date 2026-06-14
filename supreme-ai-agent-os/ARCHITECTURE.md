# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Supreme AI Agent OS                       │
├─────────────────────┬───────────────────────────────────────┤
│   Next.js Frontend  │         FastAPI Backend                │
│   (port 3000)       │         (port 8000)                    │
│                     │                                         │
│  Pages:             │  Core:                                  │
│  /overview          │  ├── Inception Layer (intent→agent)     │
│  /agents            │  ├── Soul Quality Gate                  │
│  /tasks             │  ├── Heartbeat Monitor                  │
│  /bounties          │  ├── UAC (identity/user/memory)         │
│  /browser           │  └── WebSocket Hub (/ws)               │
│  /terminal          │                                         │
│  /approvals         │  Agents (11):                           │
│  /revenue           │  executive, planner, researcher,        │
│  /payments          │  builder, browser, bounty_hunter,       │
│  /logs              │  reward_scout, memory_agent,            │
│  /connectors        │  monitor, telegram_agent, executor      │
│  /settings          │                                         │
└─────────────────────┤  Browser Engine (auto-select):          │
                      │  playwright_system > playwright_bundled │
                      │  > playwright_remote > selenium > httpx │
                      │                                         │
                      │  Connectors (14):                       │
                      │  Tool integrations: telegram, github,   │
                      │  supabase, google, notion, airtable,    │
                      │  slack, stripe                          │
                      │  Bounty platforms: bugcrowd, intigriti, │
                      │  yeswehack, open_bug_bounty, gitcoin,   │
                      │  huntr                                  │
                      │                                         │
                      │  Persistence:                           │
                      │  SQLite (memory.db) — always on         │
                      │  Redis — optional short-term cache      │
                      │                                         │
                      │  LLM Providers (auto-select):           │
                      │  Ollama > XAI > Gemini > OpenAI >       │
                      │  Groq > OpenRouter > Together           │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### Inception Layer (`backend/app/inception.py`)
Entry point for all agent tasks. Classifies intent, decomposes into subtasks,
routes to the right agent, runs with retries, scores with Soul, saves outcome.

### Soul Quality Gate (`backend/app/uac/soul/soul.py`)
Evaluates agent outputs for quality, safety, and alignment before returning.
Scores 0–1. Failed tasks are flagged for review.

### Browser Automation (`backend/app/browser.py`)
Multi-engine browser layer. Auto-detects best available engine:
1. Playwright + system Chromium (Docker default)
2. Playwright + bundled Chromium
3. Playwright → remote Chrome (Browserless)
4. Selenium + chromedriver
5. httpx (last resort, HTML-only)

### Memory Layer (`backend/app/memory/`)
SQLite via SQLAlchemy async. Tables: events, outcomes, conversations, agent_state.
No Postgres required. Migrates automatically.

### Connector Registry (`backend/app/connectors/`)
Platform connectors declare mode, auth, and capability honestly.
Registry at `/bounty-platforms` — shows live credential status.

## Data Flow

```
User request → Next.js UI
    → POST /tasks or /inception/run
    → Inception: classify intent
    → Decompose into subtasks
    → Dispatch to agents (parallel or sequential)
    → Each agent uses tools (browser/terminal/http/code)
    → Soul gates output quality
    → Save to SQLite memory
    → Return to UI via HTTP or WebSocket
```
