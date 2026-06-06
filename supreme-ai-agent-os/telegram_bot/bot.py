"""
Supreme AI Agent OS — Full Telegram Bridge
All commands + plain text as AI tasks + inline results
"""
import asyncio, json, os, sys, time
import httpx

TOK = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED = [u.strip() for u in os.environ.get("TELEGRAM_ALLOWED_USERS", "").split(",") if u.strip()]
API = os.environ.get("SUPREME_API_URL", "http://127.0.0.1:8000")
TG = f"https://api.telegram.org/bot{TOK}"

if not TOK:
    print("[telegram] TELEGRAM_BOT_TOKEN not set — bot disabled")
    sys.exit(0)

async def send(chat_id, text, parse_mode="Markdown"):
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    async with httpx.AsyncClient(timeout=15) as c:
        for chunk in chunks:
            try:
                await c.post(f"{TG}/sendMessage", json={
                    "chat_id": chat_id, "text": chunk, "parse_mode": parse_mode,
                    "disable_web_page_preview": True
                })
            except Exception as e:
                print(f"[send error] {e}")

async def api_get(path):
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            return (await c.get(f"{API}{path}")).json()
    except Exception as e:
        return {"error": str(e)}

async def api_post(path, data):
    try:
        async with httpx.AsyncClient(timeout=180) as c:
            return (await c.post(f"{API}{path}", json=data)).json()
    except Exception as e:
        return {"error": str(e)}

async def handle(msg: dict):
    chat = msg.get("chat", {}).get("id")
    user = str(msg.get("from", {}).get("id", ""))
    name = msg.get("from", {}).get("first_name", "User")
    text = (msg.get("text") or "").strip()
    if not chat or not text:
        return
    if ALLOWED and user not in ALLOWED:
        await send(chat, "⛔ Not authorized.")
        return

    # ── Commands ──────────────────────────────────────────────────────────────
    if text in ("/start", "/help"):
        await send(chat, f"""⚡ *Supreme AI Agent OS*
Hello {name}! I'm your autonomous AI agent.

*Commands:*
/status — system health
/agents — list agents  
/tasks — recent tasks
/models — LLM models
/memory — memory stats
/logs — recent logs
/rewards — opportunities
/run <prompt> — queue a task
/ask <prompt> — get instant AI answer

*Or just type anything* — I'll run it as an AI task automatically.""")

    elif text == "/status":
        d = await api_get("/health")
        soul = d.get("soul", {})
        mem = d.get("memory", {})
        graph = "✅" if d.get("graph") else "⚠️"
        ollama = "✅" if d.get("startup", {}).get("ollama", {}).get("ok") else "❌"
        await send(chat, f"""*System Status*
● {'Online ✅' if d.get('status')=='ok' else 'Offline ❌'}
Version: {d.get('version','?')}
Graph: {graph} | Ollama: {ollama}
Soul quality: {soul.get('rolling_quality',1):.2f}
Events: {mem.get('events',0)} | Outcomes: {mem.get('outcomes',0)}
Redis: {'✅' if mem.get('redis') else '⚠️ off'}
Identity: `{d.get('identity','?')}`""")

    elif text == "/agents":
        agents = await api_get("/agents")
        if isinstance(agents, list):
            lines = "\n".join(f"• *{a['name']}*\n  _{a.get('role','')[:80]}_" for a in agents)
            await send(chat, f"*Agents ({len(agents)}):*\n{lines}")
        else:
            await send(chat, "❌ Could not load agents")

    elif text == "/models":
        m = await api_get("/models")
        ol = m.get("ollama", {})
        cloud = list(m.get("cloud_enabled", {}).keys())
        models_list = "\n".join(f"  • `{mod}`" for mod in ol.get("models", [])[:8])
        await send(chat, f"""*LLM Models*
Primary: `{m.get('primary','none')}`

*Ollama (Local):* {'✅ Running' if ol.get('available') else '❌ Offline'}
{models_list or '  No models installed'}

*Cloud:* {', '.join(cloud) if cloud else 'none configured'}""")

    elif text in ("/tasks", "/tasks 10"):
        tasks = await api_get("/tasks?limit=10")
        if isinstance(tasks, list) and tasks:
            lines = []
            for t in tasks[:10]:
                s = t.get("status","?")
                icon = "✅" if s=="completed" else "🔄" if s=="running" else "⏳" if s=="queued" else "❌"
                lines.append(f"{icon} `{t['id']}` {t['prompt'][:60]}")
            await send(chat, "*Recent Tasks:*\n" + "\n".join(lines))
        else:
            await send(chat, "No tasks yet. Use /run <prompt> to create one.")

    elif text == "/memory":
        s = await api_get("/api/memory")
        await send(chat, f"""*Memory Stats*
Events: {s.get('events',0)}
Outcomes: {s.get('outcomes',0)}
Conversations: {s.get('conversations',0)}
SQLite: ✅
Redis: {'✅' if s.get('redis') else '⚠️ optional'}
DB: `{s.get('db_path','?')}`""")

    elif text == "/logs":
        logs = await api_get("/logs?limit=8")
        if isinstance(logs, list):
            lines = []
            for e in logs[-8:]:
                ts = time.strftime("%H:%M", time.localtime(e.get("created",0)))
                lines.append(f"`{ts}` *{e.get('kind','')}* {str(e.get('payload',''))[:60]}")
            await send(chat, "*Recent Logs:*\n" + "\n".join(lines))
        else:
            await send(chat, "❌ Could not load logs")

    elif text == "/rewards":
        data = await api_get("/rewards")
        opps = data.get("opportunities", []) if isinstance(data, dict) else []
        if opps:
            lines = []
            for o in opps[:6]:
                lines.append(f"• *{o.get('title','')}*\n  💰 {o.get('payout','?')} | {o.get('type','?')} | {o.get('effort','?')} effort\n  {o.get('url','')}")
            await send(chat, "*Reward Opportunities:*\n\n" + "\n\n".join(lines))
        else:
            await send(chat, "No opportunities found")

    elif text.startswith("/run "):
        prompt = text[5:].strip()
        if not prompt:
            await send(chat, "Usage: /run <your task>")
            return
        await send(chat, f"⚡ Queuing task...")
        t = await api_post("/tasks", {"prompt": prompt, "agent_id": "executive"})
        tid = t.get("id", "?")
        await send(chat, f"✅ Task `{tid}` queued\n\nI'll run it in the background. Check /tasks for status.")

    elif text.startswith("/ask "):
        prompt = text[5:].strip()
        if not prompt:
            await send(chat, "Usage: /ask <question>")
            return
        await send(chat, "🤔 Thinking...")
        r = await api_post("/agent/run", {"prompt": prompt, "agent_id": "executive"})
        answer = r.get("answer", r.get("error", "No response"))
        provider = r.get("provider", "")
        score = r.get("soul_score", 0)
        footer = f"\n\n_via {provider} · quality: {score:.2f}_" if provider else ""
        await send(chat, answer[:3800] + footer)

    elif text.startswith("/"):
        await send(chat, f"Unknown command. Use /help to see all commands.")

    else:
        # Plain text = instant AI answer
        await send(chat, "🤔 Processing...")
        r = await api_post("/agent/run", {"prompt": text, "agent_id": "executive"})
        answer = r.get("answer", r.get("error", "No response"))
        provider = r.get("provider", "")
        score = r.get("soul_score", 0)
        footer = f"\n\n_via {provider} · quality: {score:.2f}_" if provider else ""
        await send(chat, answer[:3800] + footer)

async def poll():
    offset = 0
    print(f"[telegram] ✅ Bot polling — API: {API}")
    while True:
        try:
            async with httpx.AsyncClient(timeout=35) as c:
                r = await c.get(f"{TG}/getUpdates",
                    params={"offset": offset, "timeout": 30, "allowed_updates": ["message"]})
                if r.status_code != 200:
                    print(f"[telegram] HTTP {r.status_code}")
                    await asyncio.sleep(5)
                    continue
                for u in r.json().get("result", []):
                    offset = u["update_id"] + 1
                    if "message" in u:
                        asyncio.create_task(handle(u["message"]))
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[telegram] poll error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    print(f"[telegram] Starting Supreme AI Telegram Bot")
    asyncio.run(poll())
