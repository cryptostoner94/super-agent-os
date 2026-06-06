"""Supreme AI Agent OS v2.0 — Unified Entry Point"""
from __future__ import annotations
import asyncio, json, os, time, uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings, capabilities
from backend.app.api.schemas import AgentRequest, CommandRequest, LibraryItem, ArtifactRequest
from backend.app.agents.brain import run_agent
from backend.app.agents.registry import AGENTS
from backend.app.inception import run_inception_async, classify_intent, classify_agent
from backend.app.skills.registry import SKILLS
from backend.app.runtime.executor import execute
from backend.app.artifacts.factory import create_markdown, create_html, create_xlsx, create_csv
from backend.app.memory.store import load_state, add_library
from backend.app.connectors.status import connector_status
from backend.app.ws_hub import hub

from backend.app.uac.bootstrap.bootstrap import boot
from backend.app.uac.identity.identity import Identity
from backend.app.uac.soul.soul import Soul
from backend.app.uac.heartbeat.heartbeat import Heartbeat

from backend.app.memory import init_db, log_event, get_events, get_outcomes, memory_stats

# First-run secret + directory initialization (idempotent)
from backend.app.startup import initialize as _init_runtime, validate as _validate_runtime
_runtime_secrets = _init_runtime()

try:
    from backend.app.metrics import REQUEST_COUNT, AGENT_RUNS
    from prometheus_client import make_asgi_app
    _metrics_ok = True
except Exception:
    _metrics_ok = False

_UAC_ROOT = Path(os.getenv("UAC_ROOT", str(Path.home() / ".supreme-os")))
_boot_ctx = boot(_UAC_ROOT)
_identity = Identity(_UAC_ROOT / "state")
_id_card  = _identity.load_or_create()
_soul     = Soul()
_heartbeat = Heartbeat(_boot_ctx.limits, period_s=10.0)

# User layer
from backend.app.uac.user.user import User as _User, UserProfile as _UserProfile
_user_layer = _User(_UAC_ROOT / "state")
_user_profile = _user_layer.load_or_create()

_graph = None

# Persistent settings store
_SETTINGS_PATH = Path(os.getenv("SUPREME_DB_DIR", str(Path.home() / ".supreme-os" / "state"))) / "settings.json"
def _load_settings() -> dict:
    try:
        if _SETTINGS_PATH.exists():
            return json.loads(_SETTINGS_PATH.read_text())
    except Exception:
        pass
    return {"ollama_model": "auto", "max_parallel_tasks": 4, "guardrails_strict": True, "theme": "dark"}

def _save_settings(data: dict) -> None:
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_PATH.write_text(json.dumps(data, indent=2))

# ── In-memory task store ──────────────────────────────────────────────────────
_tasks: dict[str, dict] = {}
_task_counter = 0


def _new_task(prompt: str, agent_id: str = "executive") -> dict:
    global _task_counter
    _task_counter += 1
    tid = str(_task_counter)
    task = {
        "id": tid,
        "prompt": prompt,
        "agent_id": agent_id,
        "status": "queued",
        "created": time.time(),
        "started": None,
        "finished": None,
        "result": None,
    }
    _tasks[tid] = task
    return task


async def _execute_task(tid: str):
    task = _tasks.get(tid)
    if not task:
        return
    task["status"] = "running"
    task["started"] = time.time()
    await log_event("task_start", {"id": tid, "prompt": task["prompt"][:200]})
    await hub.broadcast({"type": "task_update", "data": {"id": tid, "status": "running"}})
    try:
        result = await run_inception_async(task["prompt"], agent_id=task["agent_id"])
        task["result"] = result
        task["status"] = "completed"
    except Exception as e:
        task["result"] = {"error": str(e)}
        task["status"] = "failed"
    finally:
        task["finished"] = time.time()
        await log_event("task_finish", {"id": tid, "status": task["status"]})
        await hub.broadcast({"type": "task_update", "data": {"id": tid, "status": task["status"]}})


async def _soul_pulse():
    sig = _soul.health_signal()
    _soul.tick()
    await hub.broadcast({"type": "soul_pulse", "data": sig})


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _graph
    await init_db()
    try:
        from backend.app.graph import build_graph
        _graph = build_graph()
        await log_event("startup", {"graph": "ok", "version": "2.0.0"})
    except Exception as e:
        await log_event("startup", {"graph": "unavailable", "reason": str(e)})
    _heartbeat.register(_soul_pulse)
    hb = asyncio.create_task(_heartbeat.run_forever())
    yield
    _heartbeat.stop()
    hb.cancel()


app = FastAPI(title="Supreme AI Agent OS", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as _Req

class _RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: _Req, call_next):
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())[:8]
        response = await call_next(request)
        response.headers["x-request-id"] = rid
        return response

app.add_middleware(_RequestIdMiddleware)

if _metrics_ok:
    try:
        app.mount("/metrics", make_asgi_app())
    except Exception:
        pass

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/")
@app.get("/health")
async def health():
    mem = await memory_stats()
    return {
        "status": "ok",
        "version": "2.0.0",
        "service": settings.app_name,
        "time": time.time(),
        "identity": _identity.fingerprint(_id_card),
        "soul": _soul.health_signal(),
        "heartbeat": _heartbeat.stats.snapshot(),
        "memory": mem,
        "graph": _graph is not None,
    }

@app.get("/ready")
async def ready():
    return {"ready": True}

@app.get("/live")
async def live():
    return {"alive": True}

@app.get("/capabilities")
def get_capabilities():
    return capabilities()

@app.get("/agents")
@app.get("/api/agents")
def get_agents():
    return AGENTS

@app.get("/skills")
def get_skills():
    return SKILLS

@app.get("/connectors")
def get_connectors():
    return connector_status()

@app.get("/state")
def state():
    return load_state()

@app.get("/identity")
def identity():
    return {**_id_card.to_dict(), "fingerprint": _identity.fingerprint(_id_card)}

@app.get("/soul")
def soul_status():
    return _soul.health_signal()

@app.get("/user")
def user_get():
    return _user_profile.to_dict()

@app.post("/user")
def user_update(payload: dict):
    global _user_profile
    data = _user_profile.to_dict()
    for k, v in payload.items():
        if k in data:
            data[k] = v
    _user_profile = _UserProfile(**data)
    _user_layer.save(_user_profile)
    return _user_profile.to_dict()

@app.get("/settings")
def settings_get():
    return _load_settings()

@app.post("/settings")
def settings_update(payload: dict):
    cfg = _load_settings()
    cfg.update({k: v for k, v in payload.items() if k in cfg})
    _save_settings(cfg)
    return cfg

# ── Startup diagnostics ───────────────────────────────────────────────────────
async def _startup_check() -> dict:
    import sys
    checks: dict = {}

    checks["python"] = {"ok": True, "version": sys.version.split()[0]}

    try:
        stats = await memory_stats()
        checks["memory_db"] = {"ok": True, "note": stats.get("db_path", "")}
    except Exception as e:
        checks["memory_db"] = {"ok": False, "error": str(e)}

    try:
        from backend.app.providers.ollama import status as ol_status
        ol = ol_status()
        checks["ollama"] = {
            "ok": ol.get("available", False),
            "best": ol.get("best"),
            "degraded": not ol.get("available"),
        }
    except Exception as e:
        checks["ollama"] = {"ok": False, "degraded": True, "error": str(e)}

    checks["langgraph"] = {
        "ok": _graph is not None,
        "degraded": _graph is None,
        "note": "optional" if _graph is None else "active",
    }

    try:
        from backend.app.browser import status as bs
        bstat = await bs()
        checks["browser"] = {
            "ok": bstat.get("available", False),
            "degraded": not bstat.get("available"),
            "note": bstat.get("engine", bstat.get("error", "")),
        }
    except Exception as e:
        checks["browser"] = {"ok": False, "degraded": True, "error": str(e)}

    try:
        import redis.asyncio as aioredis
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = aioredis.from_url(url, socket_connect_timeout=1)
        await r.ping()
        await r.aclose()
        checks["redis"] = {"ok": True, "note": "connected"}
    except Exception:
        checks["redis"] = {"ok": False, "degraded": True, "note": "optional"}

    tok = os.getenv("TELEGRAM_BOT_TOKEN", "")
    checks["telegram"] = {"ok": bool(tok), "degraded": not bool(tok), "note": "optional"}

    caps = capabilities()
    cloud = {k: v for k, v in caps["llm"].items() if v}
    ol_ok = checks.get("ollama", {}).get("ok", False)
    checks["llm"] = {
        "ok": ol_ok or bool(cloud),
        "best": checks.get("ollama", {}).get("best") or (list(cloud.keys())[0] if cloud else "none"),
    }

    checks["_summary"] = {
        "total": len(checks) - 1,
        "ok": sum(1 for k, v in checks.items() if k != "_summary" and v.get("ok", False)),
    }
    return checks


@app.get("/startup")
async def startup_status():
    return await _startup_check()

@app.get("/api/secrets/validate")
def secrets_validate():
    """
    Validate that all first-run secrets and directories exist.
    Returns check results — never returns secret values.
    """
    checks = _validate_runtime()
    total  = len(checks)
    passed = sum(1 for v in checks.values() if v.get("ok", False))
    return {
        "ok": passed == total,
        "passed": passed,
        "total": total,
        "instance_id": _runtime_secrets.instance_id(),
        "fingerprint": _runtime_secrets.identity_fingerprint(),
        "checks": checks,
    }

@app.get("/api/status")
async def api_status():
    mem = await memory_stats()
    return {
        "status": "ok",
        "version": "2.0.0",
        "agents": len(AGENTS),
        "skills": len(SKILLS),
        "tasks_total": len(_tasks),
        "tasks_running": sum(1 for t in _tasks.values() if t["status"] == "running"),
        "memory": mem,
        "soul": _soul.health_signal(),
    }

# ── Models ────────────────────────────────────────────────────────────────────
@app.get("/models")
def get_models():
    from backend.app.providers.ollama import status as ol_status
    ollama = ol_status()
    caps = capabilities()
    cloud = {k: v for k, v in caps["llm"].items() if v}
    return {
        "ollama": ollama,
        "cloud_enabled": cloud,
        "primary": (
            f"ollama/{ollama.get('best')}" if ollama.get("best")
            else (list(cloud.keys())[0] if cloud else "none")
        ),
    }

# ── Browser ───────────────────────────────────────────────────────────────────
@app.get("/browser/status")
@app.get("/api/browser/status")
async def browser_status():
    from backend.app.browser import status as bs
    return await bs()

@app.post("/browser/fetch")
@app.post("/api/browser/open")
async def browser_fetch(payload: dict):
    from backend.app.browser import fetch_page
    url = payload.get("url")
    if not url:
        raise HTTPException(400, "url required")
    cookies = payload.get("cookies")
    storage_state = payload.get("storage_state")
    return await fetch_page(url, cookies=cookies, storage_state=storage_state)

@app.post("/browser/extract")
@app.post("/api/browser/extract")
async def browser_extract(payload: dict):
    from backend.app.browser import extract_text
    url = payload.get("url")
    if not url:
        raise HTTPException(400, "url required")
    return await extract_text(url)

@app.post("/browser/screenshot")
@app.post("/api/browser/screenshot")
async def browser_screenshot(payload: dict):
    from backend.app.browser import screenshot as take_screenshot
    url = payload.get("url")
    if not url:
        raise HTTPException(400, "url required")
    return await take_screenshot(url, full_page=payload.get("full_page", False))

@app.post("/browser/click")
async def browser_click(payload: dict):
    from backend.app.browser import click as do_click
    url, selector = payload.get("url"), payload.get("selector")
    if not url or not selector:
        raise HTTPException(400, "url and selector required")
    return await do_click(url, selector)

@app.post("/browser/type")
async def browser_type(payload: dict):
    from backend.app.browser import type_text
    url, selector, text = payload.get("url"), payload.get("selector"), payload.get("text", "")
    if not url or not selector:
        raise HTTPException(400, "url and selector required")
    return await type_text(url, selector, text, submit=payload.get("submit", False))

@app.post("/browser/upload")
async def browser_upload(payload: dict):
    from backend.app.browser import upload_file
    url, selector, path = payload.get("url"), payload.get("selector"), payload.get("file_path")
    if not url or not selector or not path:
        raise HTTPException(400, "url, selector, and file_path required")
    return await upload_file(url, selector, path)

@app.post("/browser/download")
async def browser_download(payload: dict):
    from backend.app.browser import download_file
    url = payload.get("url")
    if not url:
        raise HTTPException(400, "url required")
    return await download_file(url, save_dir=payload.get("save_dir", "data/artifacts"))

@app.post("/browser/cookies")
async def browser_cookies(payload: dict):
    from backend.app.browser import get_cookies
    url = payload.get("url")
    if not url:
        raise HTTPException(400, "url required")
    return await get_cookies(url)

@app.post("/browser/tabs")
async def browser_tabs(payload: dict):
    from backend.app.browser import multi_tab
    urls = payload.get("urls", [])
    if not urls:
        raise HTTPException(400, "urls list required")
    return await multi_tab(urls)

@app.post("/browser/login")
async def browser_login(payload: dict):
    from backend.app.browser import login_session
    url = payload.get("url")
    if not url:
        raise HTTPException(400, "url required")
    return await login_session(
        url,
        username_sel=payload.get("username_selector", "input[name='username']"),
        password_sel=payload.get("password_selector", "input[name='password']"),
        username=payload.get("username", ""),
        password=payload.get("password", ""),
        submit_sel=payload.get("submit_selector"),
    )

@app.post("/browser/summarize")
async def browser_summarize(payload: dict):
    from backend.app.browser import summarize_page
    url = payload.get("url")
    if not url:
        raise HTTPException(400, "url required")
    return await summarize_page(url)

@app.post("/browser/structured")
async def browser_structured(payload: dict):
    from backend.app.browser import structured_extract
    url = payload.get("url")
    schema = payload.get("schema", {"title": "h1", "description": "p"})
    if not url:
        raise HTTPException(400, "url required")
    return await structured_extract(url, schema)

@app.post("/browser/form_plan")
@app.post("/api/browser/plan")
async def browser_form_plan(payload: dict):
    from backend.app.browser import plan_form_interaction
    url = payload.get("url")
    goal = payload.get("goal", "understand the form")
    if not url:
        raise HTTPException(400, "url required")
    return await plan_form_interaction(url, goal)

@app.post("/browser/navigate")
async def browser_navigate(payload: dict):
    from backend.app.browser import navigate
    url = payload.get("url")
    selector = payload.get("selector", "")
    if not url:
        raise HTTPException(400, "url required")
    return await navigate(url, selector)

@app.post("/browser/script")
async def browser_script(payload: dict):
    from backend.app.browser import run_script
    return await run_script(payload.get("url", ""), payload.get("js", "document.title"))

# ── Task Queue ────────────────────────────────────────────────────────────────
@app.get("/tasks")
async def list_tasks(limit: int = 20):
    tasks = sorted(_tasks.values(), key=lambda t: t["created"], reverse=True)
    return tasks[:limit]

@app.post("/tasks")
async def create_task(payload: dict):
    prompt = payload.get("prompt", "")
    agent_id = payload.get("agent_id", "executive")
    if not prompt:
        raise HTTPException(400, "prompt required")
    task = _new_task(prompt, agent_id)
    asyncio.create_task(_execute_task(task["id"]))
    return task

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task not found")
    return task

# ── Memory / Logs ─────────────────────────────────────────────────────────────
@app.get("/api/memory")
async def api_memory():
    return await memory_stats()

@app.get("/memory/stats")
async def mem_stats():
    return await memory_stats()

@app.get("/logs")
async def logs(limit: int = 50):
    return await get_events(limit)

@app.get("/memory/events")
async def mem_events(limit: int = 50):
    return await get_events(limit)

@app.get("/memory/outcomes")
async def mem_outcomes(agent: Optional[str] = None, limit: int = 50):
    return await get_outcomes(agent, limit)

# ── Tools ─────────────────────────────────────────────────────────────────────
@app.get("/api/tools")
def list_tools():
    return [
        {"id": "web", "name": "Web Search"},
        {"id": "http", "name": "HTTP Client"},
        {"id": "code", "name": "Code Executor"},
        {"id": "files", "name": "File Manager"},
        {"id": "stripe_tools", "name": "Stripe Payments"},
        {"id": "email_tools", "name": "Email"},
        {"id": "telegram_tools", "name": "Telegram"},
        {"id": "apollo_tools", "name": "Apollo CRM"},
        {"id": "hunter_tools", "name": "Hunter.io"},
        {"id": "mastodon_tools", "name": "Mastodon"},
        {"id": "buffer_tools", "name": "Buffer Social"},
        {"id": "usdc_tools", "name": "USDC Payments"},
        {"id": "hackerone_tools", "name": "HackerOne"},
    ]

# ── Rewards ───────────────────────────────────────────────────────────────────
_REWARDS = [
    {
        "title": "HackerOne — Web App Pentesting",
        "type": "bug_bounty",
        "effort": "medium",
        "payout": "$100–$15,000",
        "description": "Find vulnerabilities in web apps listed on HackerOne. XSS, IDOR, SQLi most valued.",
        "url": "https://hackerone.com/opportunities",
    },
    {
        "title": "Bugcrowd — API Security Testing",
        "type": "bug_bounty",
        "effort": "medium",
        "payout": "$50–$10,000",
        "description": "API endpoint security testing across 100+ programs on Bugcrowd platform.",
        "url": "https://bugcrowd.com/engagements",
    },
    {
        "title": "Gitcoin — Open Source Bounties",
        "type": "bounty",
        "effort": "medium",
        "payout": "$50–$5,000",
        "description": "Solve open GitHub issues with bounties attached. Python, Rust, Solidity.",
        "url": "https://gitcoin.co/explorer",
    },
    {
        "title": "Lablab.ai — AI Hackathon",
        "type": "hackathon",
        "effort": "high",
        "payout": "$500–$10,000",
        "description": "Build AI apps with Anthropic, OpenAI, or open-source models. Weekly events.",
        "url": "https://lablab.ai/event",
    },
    {
        "title": "AI Grant — Research Funding",
        "type": "grant",
        "effort": "high",
        "payout": "$1,000–$50,000",
        "description": "Apply for AI research grants from foundations and tech companies.",
        "url": "https://aigrant.com",
    },
    {
        "title": "Upwork — AI/ML Freelance",
        "type": "freelance",
        "effort": "low",
        "payout": "$25–$200/hr",
        "description": "Freelance AI agent development, LangChain, prompt engineering, RAG systems.",
        "url": "https://upwork.com",
    },
    {
        "title": "Immunefi — Web3 Bug Bounties",
        "type": "bug_bounty",
        "effort": "high",
        "payout": "$1,000–$1,000,000",
        "description": "Smart contract and DeFi protocol security. Highest-paying bug bounties in Web3.",
        "url": "https://immunefi.com/explore",
    },
    {
        "title": "Fiverr — AI Automation Services",
        "type": "freelance",
        "effort": "low",
        "payout": "$50–$500/project",
        "description": "Offer AI chatbot setup, automation scripts, data analysis services.",
        "url": "https://fiverr.com",
    },
]

@app.get("/rewards")
def get_rewards():
    return {"opportunities": _REWARDS, "count": len(_REWARDS)}

# ── Bug Bounty Planner ────────────────────────────────────────────────────────
_bounty_plans: dict[str, dict] = {}

OWASP_CHECKS = [
    "A01 – Broken Access Control",
    "A02 – Cryptographic Failures",
    "A03 – Injection (SQLi, XSS, SSTI)",
    "A04 – Insecure Design",
    "A05 – Security Misconfiguration",
    "A06 – Vulnerable & Outdated Components",
    "A07 – Identification & Authentication Failures",
    "A08 – Software & Data Integrity Failures",
    "A09 – Security Logging & Monitoring Failures",
    "A10 – Server-Side Request Forgery (SSRF)",
    "Business Logic Flaws",
    "IDOR / Authorization bypass",
    "API rate limiting & abuse",
    "Information disclosure / path traversal",
]

@app.post("/bounty/plan")
async def create_bounty_plan(payload: dict):
    program = payload.get("program", "Unknown")
    scope = payload.get("scope", "")
    plan_id = str(uuid.uuid4())[:8]
    plan = {
        "id": plan_id,
        "program": program,
        "scope": scope,
        "created": time.time(),
        "checks": [
            {"id": i, "name": c, "status": "pending", "finding": None}
            for i, c in enumerate(OWASP_CHECKS)
        ],
    }
    _bounty_plans[plan_id] = plan
    await log_event("bounty_plan_created", {"id": plan_id, "program": program})
    return plan

@app.get("/bounty/plans")
def list_bounty_plans():
    return list(_bounty_plans.values())

@app.get("/bounty/plans/{plan_id}")
def get_bounty_plan(plan_id: str):
    plan = _bounty_plans.get(plan_id)
    if not plan:
        raise HTTPException(404, "plan not found")
    return plan

# ── Inception (SMARTY AI coordination layer) ──────────────────────────────────
@app.post("/inception/run")
async def inception_run(payload: dict):
    """
    Full SMARTY AI Inception run:
    intent classify → decompose → multi-agent execute → soul verify → report
    """
    prompt = payload.get("prompt", "")
    agent_id = payload.get("agent_id")
    raw_data = payload.get("raw_data", "")
    file_text = payload.get("file_text", "")
    if not prompt:
        raise HTTPException(400, "prompt required")
    if _metrics_ok:
        try:
            REQUEST_COUNT.inc()
        except Exception:
            pass
    result = await run_inception_async(prompt, agent_id, raw_data, file_text)
    await log_event("inception_run", {
        "intent": result.get("intent"),
        "agent": result.get("agent"),
        "prompt": prompt[:200],
        "score": result.get("soul_score", 0),
        "subtasks": result.get("subtasks", 1),
    })
    return result

@app.get("/inception/classify")
def inception_classify(prompt: str):
    """Classify prompt intent and recommended agent."""
    intent = classify_intent(prompt)
    agent = classify_agent(prompt)
    return {"prompt": prompt[:200], "intent": intent, "agent": agent}

# ── Agent Run ─────────────────────────────────────────────────────────────────
@app.post("/agent/run")
async def agent_run(req: AgentRequest):
    if _metrics_ok:
        try:
            REQUEST_COUNT.inc()
        except Exception:
            pass
    result = run_agent(req.prompt, req.raw_data, req.file_text, req.agent_id)
    # Soul score already included by inception layer; add it if missing
    if "soul_score" not in result:
        wu = {
            "status": "ok" if result.get("status") == "ok" else "error",
            "errors": [] if result.get("status") == "ok" else [str(result.get("answer", ""))],
            "outputs": {"answer": result.get("answer", "")},
            "duration_ms": result.get("elapsed_ms", 0),
            "attempts": 1,
        }
        verdict = _soul.evaluate(wu)
        result["soul_score"] = verdict.score
        result["soul_passed"] = verdict.passed
    await log_event("agent_run", {
        "agent": req.agent_id,
        "prompt": req.prompt[:200],
        "score": result.get("soul_score", 0),
        "intent": result.get("intent", ""),
    })
    return result

@app.post("/system/exec")
def system_exec(req: CommandRequest):
    return execute(req.command, req.timeout)

@app.post("/library/add")
def library_add(req: LibraryItem):
    item = {
        "id": str(uuid.uuid4()),
        "title": req.title,
        "type": req.type,
        "content": req.content,
        "created": time.time(),
    }
    return {"ok": True, "item": add_library(item)}

@app.post("/artifact/create")
@app.post("/api/artifacts")
async def artifact_create(req: ArtifactRequest):
    fmt = req.format.lower().strip()
    if fmt == "html":
        result = create_html(req.title, req.content)
    elif fmt == "xlsx":
        result = create_xlsx(req.content)
    elif fmt == "csv":
        result = create_csv(req.content)
    else:
        result = create_markdown(req.title, req.content)
    await log_event("artifact_created", {"title": req.title, "format": fmt})
    return result

@app.get("/api/artifacts")
def list_artifacts():
    from pathlib import Path
    artifact_dir = Path(settings.workspace_dir) / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for f in sorted(artifact_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:50]:
        if f.is_file():
            files.append({
                "name": f.name,
                "size_bytes": f.stat().st_size,
                "modified": f.stat().st_mtime,
                "format": f.suffix.lstrip(".") or "txt",
            })
    return {"artifacts": files, "count": len(files)}

# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(websocket)
