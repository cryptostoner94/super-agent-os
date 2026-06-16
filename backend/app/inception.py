"""
SMARTY AI — INCEPTION LAYER
============================
Unified coordination controller for the Supreme AI Agent OS.

Responsibilities:
  1. Parse & classify user intent
  2. Decompose goal into subtasks
  3. Select agents + tools (including REAL browser execution)
  4. Check memory for relevant context
  5. Execute subtasks with retries
  6. Verify result via Soul quality gate
  7. Save artifact
  8. Return structured outcome report
"""
from __future__ import annotations

import asyncio
import json
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from backend.app.providers.router import complete as llm_complete
from backend.app.uac.soul.soul import Soul

# ── Intent classification ─────────────────────────────────────────────────────

INTENTS = {
    "code":        ["write", "build", "code", "script", "function", "class", "refactor", "debug", "fix"],
    "research":    ["research", "find", "search", "look up", "what is", "explain", "analyze", "compare", "investigate"],
    "browser":     ["browse", "visit", "scrape", "screenshot", "navigate", "open url", "fetch page", "go to", "web page", "website", "http"],
    "bounty":      ["vulnerability", "pentest", "security", "bug bounty", "owasp", "xss", "sqli", "authorized", "bounty hunt", "yeswehack", "hackerone", "bugcrowd", "intigriti", "immunefi"],
    "reward":      ["earn", "money", "income", "freelance", "hackathon", "grant", "opportunity", "find bounty", "find reward", "revenue", "profit", "payout"],
    "memory":      ["remember", "recall", "history", "what did", "last time", "previous", "past"],
    "plan":        ["plan", "strategy", "roadmap", "steps", "how to", "guide", "checklist", "outline"],
    "monitor":     ["monitor", "watch", "alert", "status", "health", "uptime", "check", "ping"],
    "social":      ["tweet", "twitter", "post", "x.com", "social media", "publish", "share on"],
    "telegram":    ["telegram", "bot", "message", "notify", "send"],
    "general":     [],
}

def classify_intent(prompt: str) -> str:
    p = prompt.lower()
    scores: dict[str, int] = {}
    for intent, keywords in INTENTS.items():
        scores[intent] = sum(1 for kw in keywords if kw in p)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"

AGENT_FOR_INTENT = {
    "code":     "builder",
    "research": "researcher",
    "browser":  "browser",
    "bounty":   "bounty_hunter",
    "reward":   "reward_scout",
    "memory":   "memory_agent",
    "plan":     "planner",
    "monitor":  "monitor",
    "social":   "telegram_agent",
    "telegram": "telegram_agent",
    "general":  "executive",
}

# ── Decomposition ─────────────────────────────────────────────────────────────

DECOMPOSE_PROMPT = """\
You are an elite task strategist. Break the goal into at most 4 clear sequential subtasks.
Assign each subtask to the best agent. Think step-by-step about dependencies.
Return ONLY valid JSON: {{"tasks":[{{"id":1,"action":"...","agent":"...","why":"..."}}]}}
Available agents: planner, researcher, builder, browser, bounty_hunter, reward_scout, executor, memory_agent, monitor, telegram_agent, executive
For tasks requiring web data, always include a browser subtask FIRST to fetch the real data.
Goal: {goal}"""

def _decompose(goal: str) -> list[dict]:
    try:
        resp = llm_complete(DECOMPOSE_PROMPT.format(goal=goal[:800]))
        raw = resp.get("text", "")
        start = raw.find("{")
        if start >= 0:
            data = json.loads(raw[start:raw.rfind("}") + 1])
            tasks = data.get("tasks", [])
            if tasks and isinstance(tasks, list):
                return tasks
    except Exception:
        pass
    return [{"id": 1, "action": goal, "agent": classify_agent(goal), "why": "direct execution"}]

def classify_agent(goal: str) -> str:
    return AGENT_FOR_INTENT.get(classify_intent(goal), "executive")

# ── Tool selection ────────────────────────────────────────────────────────────

TOOL_HINTS = {
    "code":     ["code", "files"],
    "research": ["web", "browser", "http"],
    "browser":  ["browser", "playwright"],
    "bounty":   ["browser", "http", "web"],
    "reward":   ["browser", "web", "http"],
    "social":   ["twitter", "telegram"],
    "plan":     [],
    "general":  [],
}

def select_tools(intent: str) -> list[str]:
    return TOOL_HINTS.get(intent, [])

# ── Elite Agent Prompts ───────────────────────────────────────────────────────

AGENT_PROMPTS: dict[str, str] = {
    "planner": """You are an elite strategic master planner with expert-level knowledge in project management, systems design, and execution strategy.

Your output MUST include:
1. **Goal Analysis**: Break down the core objective, constraints, and success criteria
2. **Phased Execution Plan**: 3-7 clear phases with specific deliverables per phase
3. **Task Dependencies**: Which tasks must complete before others can start
4. **Risk Matrix**: Top 3 risks with mitigation strategy for each
5. **Resource Requirements**: Tools, APIs, time estimates, and agent assignments
6. **Success Metrics**: How to measure if each phase succeeded
7. **Contingency Paths**: What to do if the primary path fails

Be specific, actionable, and comprehensive. No vague guidance.""",

    "researcher": """You are an elite research intelligence analyst with expertise in web research, data synthesis, competitive analysis, and fact verification.

Your research MUST:
1. **Synthesize multiple perspectives** — cover mainstream, contrarian, and niche viewpoints
2. **Cite specific sources** — name platforms, publications, or data sources
3. **Quantify everything** — use numbers, percentages, dates, prices, rankings where available
4. **Separate facts from analysis** — clearly distinguish verified facts from your interpretation
5. **Identify gaps** — note what couldn't be verified and why
6. **Actionable conclusion** — end with 3-5 specific, concrete next steps the user can take TODAY
7. **Competitive landscape** — if applicable, rank top players by capability/price/adoption

Structure: Executive Summary → Key Findings → Deep Analysis → Actionable Recommendations""",

    "builder": """You are a senior software architect and full-stack engineer with expertise in production-grade systems, security, and performance.

Your code MUST:
1. **Production-ready** — proper error handling, logging, and graceful failure modes
2. **Secure by default** — no hardcoded credentials, proper input validation, no injection vectors
3. **Well-structured** — clear module organization, separation of concerns, DRY principles
4. **Tested** — include unit tests or at minimum test cases for edge cases
5. **Deployable** — include requirements.txt/package.json updates if needed
6. **Performant** — async where appropriate, efficient algorithms, proper resource cleanup

Always output: Architecture overview → Complete code → Usage examples → Testing approach""",

    "browser": """You are an elite web intelligence agent with deep expertise in browser automation, web scraping, data extraction, and online research.

When REAL page content is provided to you, you MUST:
1. **Extract maximum value** — pull out all relevant data points, prices, dates, names, links
2. **Structure the data** — organize into clear tables, lists, or categories
3. **Identify patterns** — note trends, anomalies, and opportunities in the data
4. **Verify credibility** — assess source authority and data freshness
5. **Cross-reference** — connect findings across different sections of the page
6. **Actionable insights** — translate raw data into specific recommended actions
7. **Deep analysis** — go beyond surface-level; explain WHAT the data means and WHY it matters

When no real content is available, provide detailed navigation strategy with exact URLs and selectors.""",

    "bounty_hunter": """You are an elite authorized security researcher and bug bounty hunter specializing in web application security, API security, and vulnerability research.

For EVERY security task you MUST:
1. **Scope Analysis** — precisely define in-scope and out-of-scope targets
2. **Threat Modeling** — identify the most likely attack surfaces and high-value targets
3. **OWASP Top 10 Checklist** — systematic check of all 10 categories with specific test cases
4. **Custom Attack Vectors** — identify app-specific logic flaws and business logic bugs
5. **PoC Development** — write proof-of-concept payloads/requests for each finding
6. **CVSS Scoring** — rate severity with proper CVSS 3.1 scores
7. **Professional Report** — full vulnerability report ready for submission

Focus: Authentication bypass, IDOR, XSS, SQLi, SSRF, API key exposure, rate limiting, JWT vulnerabilities, OAuth flaws.
Always operate within authorized scope only.""",

    "reward_scout": """You are an elite income optimization and opportunity discovery agent specializing in bug bounties, grants, hackathons, freelance projects, and AI/Web3 monetization.

For EVERY opportunity search you MUST:
1. **Platform Coverage** — HackerOne, Bugcrowd, YesWeHack, Intigriti, Immunefi, Gitcoin, Devfolio, DoraHacks
2. **ROI Analysis** — estimate payout/effort ratio for each opportunity
3. **Qualification Match** — assess our agent OS capabilities against requirements
4. **Deadline Tracking** — prioritize by urgency, flag closing soon
5. **Proposal Draft** — write a compelling, ready-to-submit proposal for the top opportunity
6. **Action Plan** — step-by-step instructions to capture each opportunity TODAY
7. **Income Pipeline** — organize opportunities into a prioritized revenue pipeline

Output: Opportunity Matrix → Top Pick Deep-Dive → Ready-to-Submit Proposal""",

    "executor": """You are an elite systems engineer and DevOps specialist with expertise in Linux, Docker, Python, and production deployment.

For EVERY execution task you MUST:
1. **Pre-flight Check** — verify prerequisites, dependencies, and current system state
2. **Exact Commands** — provide complete, copy-paste-ready commands with no ambiguity
3. **Safety First** — prefer reversible operations; warn clearly about destructive operations
4. **Validation Steps** — for each command, provide the verification step to confirm success
5. **Error Recovery** — for each step, provide the rollback/recovery if it fails
6. **Logging** — include logging/output capture in all scripts
7. **Completion Summary** — end with a health check confirming the task succeeded""",

    "memory_agent": """You are an elite context intelligence agent with perfect recall of all past interactions, decisions, and outcomes.

For EVERY memory task you MUST:
1. **Temporal Context** — organize relevant memories chronologically
2. **Pattern Recognition** — identify recurring themes, successes, and failures
3. **Relevant Connections** — surface non-obvious connections between past and current tasks
4. **Decision History** — recall key decisions made and their outcomes
5. **Lesson Synthesis** — distill key lessons learned that apply to the current task
6. **Confidence Rating** — rate certainty of recalled information
7. **Gap Identification** — note what information is missing from memory

Structure: Most Relevant Memories → Patterns Observed → Applied Lessons → Memory Gaps""",

    "monitor": """You are an elite SRE and observability engineer with expertise in system monitoring, alerting, and reliability engineering.

For EVERY monitoring task you MUST:
1. **Health Dashboard** — overall system health score (0-100) with component breakdown
2. **Critical Alerts** — list any conditions exceeding critical thresholds
3. **Warning Conditions** — conditions approaching thresholds
4. **Performance Metrics** — latency, throughput, error rates, resource utilization
5. **Trend Analysis** — is performance improving, degrading, or stable?
6. **Incident Playbook** — if any alert is active, provide exact steps to diagnose and fix
7. **Optimization Recommendations** — 3 specific actions to improve reliability

Alert levels: CRITICAL (action now) → WARNING (action soon) → INFO (note for later)""",

    "telegram_agent": """You are an elite Telegram bot developer and social automation specialist with expertise in the Telegram Bot API and Twitter/X API.

For social media tasks:
1. **Content Strategy** — craft message for maximum engagement and reach
2. **Optimal Format** — use proper formatting, hashtags, and mentions for the platform
3. **Timing** — identify best posting time for target audience
4. **Call to Action** — every post needs a clear CTA
5. **Thread Strategy** — if complex topic, plan a multi-tweet thread
6. **Metrics to Track** — define what success looks like for this post
7. **Follow-up Actions** — plan engagement response strategy

For Telegram bots: generate complete Python code with handlers and webhook setup.""",

    "executive": """You are the Supreme Executive Agent — the master orchestrator of all agent activities with full authority over the entire Super Agent OS.

For EVERY task you MUST:
1. **Mission Assessment** — evaluate full scope, urgency, and strategic importance
2. **Agent Delegation** — identify which specialized agents handle each component
3. **Resource Allocation** — prioritize tasks and set execution order
4. **Quality Control** — verify each agent's output meets standards
5. **Risk Management** — identify and mitigate risks proactively
6. **Cross-Agent Coordination** — ensure agents share context and build on each other's work
7. **Executive Summary** — produce a clear, actionable outcome report with next steps

Be decisive, comprehensive, and strategic. You see the full picture.""",
}

# ── Real browser execution ────────────────────────────────────────────────────

_URL_RE = re.compile(r'https?://[^\s"\'<>\])\}]+')

def _extract_url(text: str) -> str | None:
    m = _URL_RE.search(text)
    return m.group(0).rstrip(".,;:") if m else None


def _run_browser_task(action: str) -> dict:
    """Actually fetches real web content using the browser engine."""
    from backend.app.browser import fetch_page, extract_text

    # Step 1: Identify URL — either from action text or via LLM planning
    url = _extract_url(action)
    if not url:
        plan_result = llm_complete(
            f"Identify the best URL to visit for this task. "
            f"Return ONLY valid JSON: {{\"url\":\"https://...\",\"query\":\"...\"}}\n\nTask: {action[:400]}"
        )
        try:
            raw = plan_result.get("text", "")
            start = raw.find("{")
            if start >= 0:
                plan = json.loads(raw[start: raw.rfind("}") + 1])
                url = plan.get("url", "")
        except Exception:
            pass

    browser_content = ""
    browser_meta: dict = {}

    if url:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(fetch_page(url))
                if result.get("ok") or result.get("text"):
                    text = result.get("text", "")[:10000]
                    title = result.get("title", url)
                    links = result.get("links", [])[:25]
                    engine = result.get("engine", "unknown")
                    browser_content = (
                        f"[LIVE WEB DATA — fetched via {engine}]\n"
                        f"URL: {url}\nTitle: {title}\n\n"
                        f"Page Content:\n{text}\n\n"
                        f"Links ({len(links)}):\n" +
                        "\n".join(f"  - {lk.get('text','')}: {lk.get('href','')}" for lk in links[:15])
                    )
                    browser_meta = {"url": url, "engine": engine, "content_len": len(text), "browser_used": True}
                else:
                    # Fallback: plain HTTP extract
                    result2 = loop.run_until_complete(extract_text(url))
                    if result2.get("text"):
                        browser_content = f"[LIVE WEB DATA — text extract]\nURL: {url}\n\n{result2['text'][:8000]}"
                        browser_meta = {"url": url, "engine": "extract", "browser_used": True}
            finally:
                loop.close()
        except Exception as exc:
            browser_meta = {"url": url, "browser_used": False, "error": str(exc)}

    # Step 2: LLM analyzes the real content (or falls back to pure LLM)
    system = AGENT_PROMPTS["browser"]
    if browser_content:
        full_prompt = (
            f"{system}\n\n"
            f"Task: {action}\n\n"
            f"=== REAL LIVE PAGE CONTENT ===\n{browser_content}\n\n"
            f"Based on this live data, provide a comprehensive, structured analysis and complete the task:"
        )
    else:
        error_note = f"\n[Browser unavailable: {browser_meta.get('error', 'no URL found')}]"
        full_prompt = f"{system}\n\nTask: {action}{error_note}"

    result = llm_complete(full_prompt)
    return {
        "agent": "browser",
        "action": action,
        "output": result.get("text", ""),
        "provider": result.get("provider", "unknown"),
        **browser_meta,
    }


def _run_subtask(action: str, agent_id: str) -> dict:
    if agent_id == "browser":
        return _run_browser_task(action)
    system = AGENT_PROMPTS.get(agent_id, AGENT_PROMPTS["executive"])
    full_prompt = f"{system}\n\nTask: {action}"
    result = llm_complete(full_prompt)
    return {
        "agent": agent_id,
        "action": action,
        "output": result.get("text", ""),
        "provider": result.get("provider", "unknown"),
    }

# ── Outcome dataclass ─────────────────────────────────────────────────────────

@dataclass
class InceptionResult:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    goal: str = ""
    intent: str = ""
    agent: str = ""
    tools: list[str] = field(default_factory=list)
    subtasks: list[dict] = field(default_factory=list)
    results: list[dict] = field(default_factory=list)
    answer: str = ""
    soul_score: float = 1.0
    soul_passed: bool = True
    provider: str = ""
    elapsed_ms: float = 0.0
    artifact_id: str | None = None
    created: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

# ── Inception controller ──────────────────────────────────────────────────────

_soul = Soul()


def run_inception(
    prompt: str,
    agent_id: str | None = None,
    raw_data: str = "",
    file_text: str = "",
    session_id: str | None = None,
) -> dict:
    """
    Synchronous inception controller.
    Coordinates intent → decompose → execute (with real browser) → verify → report.
    """
    t0 = time.perf_counter()
    ir = InceptionResult(goal=prompt)

    # 1. Classify intent
    ir.intent = classify_intent(prompt)
    ir.agent = agent_id or classify_agent(prompt)
    ir.tools = select_tools(ir.intent)

    # 2. Decompose into subtasks (skip for short prompts)
    if len(prompt) > 120:
        ir.subtasks = _decompose(prompt)
    else:
        ir.subtasks = [{"id": 1, "action": prompt, "agent": ir.agent, "why": "direct"}]

    # 3. Execute subtasks
    errors = []
    primary_output = ""
    for subtask in ir.subtasks[:4]:  # cap at 4
        try:
            res = _run_subtask(
                subtask.get("action", prompt),
                subtask.get("agent", ir.agent),
            )
            ir.results.append(res)
            if not primary_output:
                primary_output = res.get("output", "")
            if res.get("provider"):
                ir.provider = res["provider"]
        except Exception as e:
            errors.append(str(e))
            ir.results.append({"error": str(e), "action": subtask.get("action", "")})

    # 4. Synthesize final answer
    if len(ir.subtasks) > 1 and ir.results:
        combined = "\n\n---\n\n".join(
            f"**Step {i+1} — {r.get('agent', 'agent')}:**\n{r.get('output', r.get('error', ''))}"
            for i, r in enumerate(ir.results)
        )
        ir.answer = combined
    else:
        ir.answer = primary_output or "No output produced."

    # 5. Soul quality gate
    wu = {
        "status": "ok" if not errors else "error",
        "errors": errors,
        "outputs": {"answer": ir.answer},
        "duration_ms": (time.perf_counter() - t0) * 1000,
        "attempts": 1,
    }
    verdict = _soul.evaluate(wu)
    ir.soul_score = verdict.score
    ir.soul_passed = verdict.passed

    ir.elapsed_ms = (time.perf_counter() - t0) * 1000

    return {
        "status": "ok" if not errors else "partial",
        "id": ir.id,
        "intent": ir.intent,
        "agent": ir.agent,
        "tools": ir.tools,
        "answer": ir.answer,
        "subtasks": len(ir.subtasks),
        "provider": ir.provider,
        "soul_score": ir.soul_score,
        "soul_passed": ir.soul_passed,
        "elapsed_ms": round(ir.elapsed_ms, 1),
        "results": ir.results,
    }


async def run_inception_async(
    prompt: str,
    agent_id: str | None = None,
    raw_data: str = "",
    file_text: str = "",
) -> dict:
    """Async wrapper — runs inception in a thread to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: run_inception(prompt, agent_id, raw_data, file_text),
    )
