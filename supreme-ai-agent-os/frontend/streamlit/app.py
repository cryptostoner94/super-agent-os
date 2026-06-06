"""Supreme AI Agent OS — Premium Dashboard"""
import json, os as _os, time, requests, streamlit as st
from datetime import datetime

API = _os.getenv("SUPREME_API_URL") or st.secrets.get("SUPREME_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Supreme AI", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# ── Session state ─────────────────────────────────────────────────────────────
_defaults = {"messages": [], "page": "overview", "agent": "executive"}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── API helpers ───────────────────────────────────────────────────────────────
def get(path, timeout=6):
    try: return requests.get(API + path, timeout=timeout).json()
    except: return {}

def post(path, payload, timeout=120):
    try: return requests.post(API + path, json=payload, timeout=timeout).json()
    except Exception as e: return {"error": str(e)}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*{font-family:'Inter',sans-serif!important;box-sizing:border-box}
#MainMenu,footer,header,.stDeployButton{display:none!important}
.stApp{background:#080810!important}
.block-container{padding:0!important;max-width:100%!important}

/* Sidebar */
section[data-testid="stSidebar"]{background:#0d0d1a!important;border-right:1px solid #1e1e3a!important;width:240px!important}
section[data-testid="stSidebar"] .block-container{padding:.75rem .6rem!important}

/* Logo */
.logo{font-size:1.1rem;font-weight:800;color:#a78bfa;padding:.4rem .5rem 1.2rem;display:flex;align-items:center;gap:8px;letter-spacing:-.5px}
.logo-pulse{width:8px;height:8px;background:linear-gradient(135deg,#7c3aed,#a78bfa);border-radius:50%;animation:glow 2s ease-in-out infinite}
@keyframes glow{0%,100%{opacity:1;box-shadow:0 0 4px #a78bfa}50%{opacity:.4;box-shadow:none}}

/* Nav buttons */
.stButton>button{background:transparent!important;color:#6b7280!important;border:none!important;border-radius:10px!important;text-align:left!important;padding:9px 12px!important;font-size:.88rem!important;font-weight:500!important;width:100%!important;transition:all .15s!important}
.stButton>button:hover{background:#1a1a2e!important;color:#e2e8f0!important}
.active-nav .stButton>button{background:#1e1e3a!important;color:#a78bfa!important;font-weight:600!important}

/* Content area */
.main-content{padding:24px;overflow-y:auto;height:100vh}

/* Status badges */
.badge{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:99px;font-size:.75rem;font-weight:700}
.badge.ok{background:#0d2818;color:#22c55e;border:1px solid #166534}
.badge.warn{background:#1a1200;color:#f59e0b;border:1px solid #854d0e}
.badge.err{background:#1a0808;color:#ef4444;border:1px solid #991b1b}

/* Cards */
.card{background:#0f0f1e;border:1px solid #1e1e3a;border-radius:16px;padding:20px;margin:8px 0}
.card:hover{border-color:#7c3aed33;transition:.2s}
.metric-card{background:#0f0f1e;border:1px solid #1e1e3a;border-radius:12px;padding:16px}
.metric-val{font-size:2rem;font-weight:800;color:#a78bfa;line-height:1}
.metric-lbl{font-size:.72rem;color:#6b7280;margin-top:4px;text-transform:uppercase;letter-spacing:.05em}

/* Chat messages */
.msg-ai{background:#0f0f1e;border:1px solid #1e1e3a;border-radius:16px 16px 16px 4px;padding:14px 18px;color:#e2e8f0;font-size:.9rem;line-height:1.7;max-width:780px}
.msg-user{background:linear-gradient(135deg,#4c1d95,#6d28d9);border-radius:16px 16px 4px 16px;padding:12px 18px;color:#fff;font-size:.9rem;line-height:1.6;max-width:780px;margin-left:auto}
.msg-meta{font-size:.7rem;color:#4b5563;margin-top:4px}

/* Status row */
.status-row{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}

/* Agent card */
.agent-card{background:#0f0f1e;border:1px solid #1e1e3a;border-radius:14px;padding:18px 16px;text-align:center;cursor:pointer;transition:all .2s}
.agent-card:hover{border-color:#7c3aed;background:#1a0d2e;transform:translateY(-2px)}

/* Section title */
.sec-title{font-size:1.1rem;font-weight:700;color:#e2e8f0;margin:4px 0 20px;display:flex;align-items:center;gap:8px}
.sec-title span{color:#a78bfa}

/* Task pill */
.task-pill{display:flex;align-items:center;gap:10px;background:#0f0f1e;border:1px solid #1e1e3a;border-radius:10px;padding:10px 14px;margin:4px 0;font-size:.83rem;color:#9ca3af}
.dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.dot.ok{background:#22c55e}.dot.run{background:#f59e0b;animation:pulse 1s infinite}.dot.err{background:#ef4444}.dot.q{background:#4b5563}

/* Reward card */
.reward-card{background:#0f0f1e;border:1px solid #1e1e3a;border-radius:14px;padding:16px;margin:8px 0;transition:.2s}
.reward-card:hover{border-color:#7c3aed44}

/* Input area */
.input-wrapper{position:fixed;bottom:0;left:240px;right:0;background:#080810;border-top:1px solid #1e1e3a;padding:12px 24px 16px;z-index:100}
.input-inner{max-width:820px;margin:0 auto;background:#0f0f1e;border:1px solid #2d2d4e;border-radius:16px;display:flex;align-items:flex-end;gap:8px;padding:8px 8px 8px 16px;transition:.2s}
.input-inner:focus-within{border-color:#7c3aed}

@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

/* Streamlit overrides */
.stTextArea textarea{background:transparent!important;border:none!important;color:#e2e8f0!important;font-size:.9rem!important;resize:none!important;min-height:36px!important}
.stTextArea textarea:focus{box-shadow:none!important}
.stTextInput input{background:#0f0f1e!important;border:1px solid #1e1e3a!important;color:#e2e8f0!important;border-radius:10px!important;padding:8px 12px!important}
.stTextInput input:focus{border-color:#7c3aed!important;box-shadow:none!important}
.stSelectbox>div>div{background:#0f0f1e!important;border-color:#1e1e3a!important;color:#e2e8f0!important;border-radius:10px!important}
.stTextArea label,.stTextInput label{color:#6b7280!important;font-size:.8rem!important}
.stTabs [data-baseweb="tab"]{color:#6b7280!important;background:transparent!important;border:none!important;padding:8px 16px!important}
.stTabs [aria-selected="true"]{color:#a78bfa!important;border-bottom:2px solid #a78bfa!important}
.stTabs [data-baseweb="tab-list"]{background:transparent!important;border-bottom:1px solid #1e1e3a!important}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:#2d2d4e;border-radius:4px}
hr{border-color:#1e1e3a!important}
.stSuccess>div,.stInfo>div,.stWarning>div,.stError>div{border-radius:10px!important;font-size:.85rem!important}
@media(max-width:768px){section[data-testid="stSidebar"]{display:none!important}.input-wrapper{left:0!important}}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div class='logo'><div class='logo-pulse'></div>Supreme AI</div>", unsafe_allow_html=True)

    h = get("/health", 3)
    alive = h.get("status") == "ok"
    graph = h.get("graph", False)
    soul_q = h.get("soul", {}).get("rolling_quality", 0)
    st.markdown(f"""
    <div style='background:{"#0d2818" if alive else "#1a0808"};border:1px solid {"#166534" if alive else "#991b1b"};
    border-radius:10px;padding:10px 12px;margin-bottom:16px;font-size:.8rem'>
        <div style='color:{"#22c55e" if alive else "#ef4444"};font-weight:700'>
            {"● Online" if alive else "● Offline"} · v{h.get("version","?")}
        </div>
        <div style='color:#6b7280;margin-top:2px'>
            Soul {soul_q:.2f} · Graph {"✓" if graph else "✗"} · {h.get("memory",{}).get("events",0)} events
        </div>
    </div>""", unsafe_allow_html=True)

    nav = [
        ("overview", "⚡", "Overview"),
        ("chat",     "💬", "Chat"),
        ("tasks",    "🔄", "Tasks"),
        ("agents",   "🤖", "Agents"),
        ("models",   "🧠", "Models"),
        ("memory",   "🗄️", "Memory"),
        ("rewards",  "💰", "Rewards"),
        ("bounty",   "🎯", "Bug Bounty"),
        ("browser",  "🌐", "Browser"),
        ("tools",    "🔧", "Tools"),
        ("artifacts","📦", "Artifacts"),
        ("logs",     "📋", "Logs"),
        ("settings", "⚙️", "Settings"),
    ]
    for pid, icon, label in nav:
        c = st.container()
        if st.session_state.page == pid:
            c.markdown("<div class='active-nav'>", unsafe_allow_html=True)
        if st.button(f"{icon}  {label}", key=f"nav_{pid}", use_container_width=True):
            st.session_state.page = pid
            st.rerun()
        if st.session_state.page == pid:
            c.markdown("</div>", unsafe_allow_html=True)

page = st.session_state.page

# ── OVERVIEW ─────────────────────────────────────────────────────────────────
if page == "overview":
    st.markdown("<div class='main-content'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>⚡ <span>System Overview</span></div>", unsafe_allow_html=True)

    stat = get("/api/status")
    mem  = get("/api/memory")
    models = get("/models")
    browser = get("/api/browser/status", 4)
    startup = get("/startup")

    # Metrics row
    uptime = h.get("heartbeat",{}).get("uptime_s",0)
    uptime_str = f"{uptime/3600:.1f}h" if uptime > 3600 else f"{uptime/60:.0f}m" if uptime > 60 else f"{uptime:.0f}s"
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    for col, val, lbl in [
        (c1, stat.get("agents",11), "Agents"),
        (c2, stat.get("skills",9),  "Skills"),
        (c3, stat.get("tasks_total",0), "Tasks"),
        (c4, mem.get("events",0), "Events"),
        (c5, uptime_str, "Uptime"),
        (c6, f"{soul_q:.2f}", "Soul Q"),
    ]:
        col.markdown(f"<div class='metric-card'><div class='metric-val'>{val}</div><div class='metric-lbl'>{lbl}</div></div>", unsafe_allow_html=True)

    # System status
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div style='color:#e2e8f0;font-weight:700;margin-bottom:12px'>🔋 Core Systems</div>", unsafe_allow_html=True)
        systems = [
            ("API", alive, "FastAPI backend"),
            ("LangGraph", graph, "Agent orchestration"),
            ("SQLite", mem.get("sqlite",False), "Memory persistence"),
            ("Soul Engine", soul_q > 0.8, f"Quality {soul_q:.2f}"),
        ]
        for name, ok, note in systems:
            color = "#22c55e" if ok else "#ef4444"
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #1e1e3a'>
                <span style='color:{color};font-size:1.1rem'>{"●" if ok else "○"}</span>
                <span style='color:#e2e8f0;font-weight:600;flex:1'>{name}</span>
                <span style='color:#6b7280;font-size:.75rem'>{note}</span>
                <span class='badge {"ok" if ok else "err"}'>{"OK" if ok else "OFFLINE"}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div style='color:#e2e8f0;font-weight:700;margin-bottom:12px'>🔌 Services</div>", unsafe_allow_html=True)
        ol = models.get("ollama",{})
        tg = startup.get("telegram",{})
        br = browser
        redis = mem.get("redis",False)
        services = [
            ("Ollama LLM", ol.get("available",False), ol.get("base_url","http://localhost:11434")),
            ("Browser", br.get("available",False), f"{br.get('engine','?')} ({br.get('mode','?')})"),
            ("Telegram", tg.get("ok",False), "Bot active" if tg.get("ok") else "Set TELEGRAM_BOT_TOKEN"),
            ("Redis", redis, "Connected" if redis else "SQLite fallback active"),
        ]
        for name, ok, note in services:
            deg = not ok
            color = "#22c55e" if ok else "#f59e0b" if deg else "#ef4444"
            badge_cls = "ok" if ok else "warn"
            badge_lbl = "OK" if ok else "CONFIGURE"
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #1e1e3a'>
                <span style='color:{color};font-size:1.1rem'>{"●" if ok else "○"}</span>
                <span style='color:#e2e8f0;font-weight:600;flex:1'>{name}</span>
                <span style='color:#6b7280;font-size:.75rem;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{note}</span>
                <span class='badge {badge_cls}'>{badge_lbl}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Quick actions
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='color:#e2e8f0;font-weight:700;margin-bottom:12px'>⚡ Quick Actions</div>", unsafe_allow_html=True)
    qa_cols = st.columns(4)
    quick = [
        ("💬 Start Chat", "chat"),
        ("⚡ Run Task", "tasks"),
        ("💰 Rewards", "rewards"),
        ("🎯 Bug Bounty", "bounty"),
    ]
    for (label, target), col in zip(quick, qa_cols):
        if col.button(label, key=f"qa_{target}", use_container_width=True):
            st.session_state.page = target
            st.rerun()

    # Recent events
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='color:#e2e8f0;font-weight:700;margin-bottom:12px'>📋 Recent Activity</div>", unsafe_allow_html=True)
    evts = get("/logs?limit=8")
    if isinstance(evts, list):
        for e in evts:
            ts = datetime.fromtimestamp(e.get("created",0)).strftime("%H:%M:%S")
            kind = e.get("kind","")
            is_ok = any(x in kind for x in ("ok","start","complet","creat"))
            is_err = any(x in kind for x in ("error","fail"))
            color = "#22c55e" if is_ok else "#ef4444" if is_err else "#6b7280"
            st.markdown(f"""
            <div style='display:flex;gap:12px;padding:7px 0;border-bottom:1px solid #111130;font-size:.8rem'>
                <span style='color:#4b5563;font-family:monospace;white-space:nowrap'>{ts}</span>
                <span style='color:{color};font-weight:600;white-space:nowrap;min-width:120px'>{kind}</span>
                <span style='color:#6b7280;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{str(e.get("payload",""))[:100]}</span>
            </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── CHAT ─────────────────────────────────────────────────────────────────────
elif page == "chat":
    agents_data = get("/agents")
    agent_map = {a["name"]: a["id"] for a in agents_data} if isinstance(agents_data, list) else {"Executive Agent": "executive"}

    # Chat container
    st.markdown("<div style='padding:20px 24px;padding-bottom:120px'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>💬 <span>Chat</span></div>", unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown("""
        <div style='max-width:820px;margin:40px auto;text-align:center;padding:40px 20px'>
            <div style='font-size:3rem;margin-bottom:12px'>⚡</div>
            <div style='font-size:1.5rem;font-weight:800;color:#e2e8f0;margin-bottom:8px'>Supreme AI Agent OS</div>
            <div style='color:#6b7280;font-size:.95rem;margin-bottom:40px'>Autonomous AI workspace. 11 agents. Local-first.</div>
            <div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;max-width:600px;margin:0 auto;text-align:left'>
                <div style='background:#0f0f1e;border:1px solid #1e1e3a;border-radius:12px;padding:14px;cursor:pointer'>
                    <div style='font-weight:700;color:#e2e8f0;margin-bottom:4px'>🔍 Research</div>
                    <div style='color:#6b7280;font-size:.83rem'>Research the top 5 AI agent frameworks in 2025</div>
                </div>
                <div style='background:#0f0f1e;border:1px solid #1e1e3a;border-radius:12px;padding:14px'>
                    <div style='font-weight:700;color:#e2e8f0;margin-bottom:4px'>💻 Code</div>
                    <div style='color:#6b7280;font-size:.83rem'>Write a Python FastAPI endpoint with JWT auth</div>
                </div>
                <div style='background:#0f0f1e;border:1px solid #1e1e3a;border-radius:12px;padding:14px'>
                    <div style='font-weight:700;color:#e2e8f0;margin-bottom:4px'>📊 Plan</div>
                    <div style='color:#6b7280;font-size:.83rem'>Create a deployment checklist for a FastAPI app</div>
                </div>
                <div style='background:#0f0f1e;border:1px solid #1e1e3a;border-radius:12px;padding:14px'>
                    <div style='font-weight:700;color:#e2e8f0;margin-bottom:4px'>🎯 Bounty</div>
                    <div style='color:#6b7280;font-size:.83rem'>Analyze bug bounty opportunities on HackerOne</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            role = msg["role"]
            content = msg["content"]
            meta = msg.get("meta", "")
            if role == "user":
                st.markdown(f"<div style='display:flex;justify-content:flex-end;margin:8px 0'><div class='msg-user'>{content}</div></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='margin:8px 0'><div class='msg-ai'>{content}</div><div class='msg-meta'>{meta}</div></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Fixed input bar
    st.markdown("<div class='input-wrapper'><div class='input-inner'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([5, 1.5, 1])
    with col1:
        prompt = st.text_area("", placeholder="Message Supreme AI… (Shift+Enter for newline)", height=44, label_visibility="collapsed", key="chat_input")
    with col2:
        agent_sel = st.selectbox("", list(agent_map.keys()), label_visibility="collapsed", key="agent_sel")
    with col3:
        send = st.button("Send ➤", use_container_width=True, type="primary")
    st.markdown("</div></div>", unsafe_allow_html=True)

    col_a, col_b = st.columns([6,1])
    with col_b:
        if st.button("🗑 Clear", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

    if send and prompt.strip():
        st.session_state.messages.append({"role": "user", "content": prompt.strip()})
        with st.spinner("Thinking…"):
            aid = agent_map.get(agent_sel, "executive")
            res = post("/agent/run", {"prompt": prompt.strip(), "agent_id": aid})
        answer = res.get("answer", res.get("error", "No response"))
        prov = res.get("provider","")
        score = res.get("soul_score",0) or 0
        ms = res.get("elapsed_ms",0) or 0
        meta = f"{prov} · soul {score:.2f} · {ms:.0f}ms" if prov else ""
        st.session_state.messages.append({"role": "ai", "content": answer, "meta": meta})
        st.rerun()

# ── TASKS ─────────────────────────────────────────────────────────────────────
elif page == "tasks":
    st.markdown("<div style='padding:20px 24px'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>🔄 <span>Task Queue</span></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([4,1.5,1])
    with col1:
        tp = st.text_input("New task", placeholder="Describe what you want the agent to execute…")
    with col2:
        agents = get("/agents")
        agent_names = {a["id"]: a["name"] for a in agents} if isinstance(agents, list) else {}
        ta = st.selectbox("Agent", list(agent_names.keys()), format_func=lambda x: agent_names.get(x, x)) if agent_names else st.selectbox("Agent", ["executive"])
    with col3:
        st.write("")
        queue_btn = st.button("Queue ➤", use_container_width=True, type="primary")

    if queue_btn and tp.strip():
        r = post("/tasks", {"prompt": tp.strip(), "agent_id": ta})
        if r.get("id"):
            st.success(f"✅ Task #{r['id']} queued")
        else:
            st.error(str(r.get("error", r)))

    col_r, col_s = st.columns([5,1])
    with col_s:
        if st.button("🔄 Refresh"): st.rerun()

    tasks = get("/tasks?limit=25")
    if isinstance(tasks, list) and tasks:
        for t in tasks:
            s = t.get("status","")
            dot = "ok" if s=="completed" else "run" if s=="running" else "err" if s in ("failed","timeout") else "q"
            elapsed = ""
            if t.get("started"):
                dur = (t.get("finished") or time.time()) - t["started"]
                elapsed = f" · {dur:.1f}s"
            agent_icon = next((a.get("icon","🤖") for a in (agents if isinstance(agents,list) else []) if a["id"]==t.get("agent_id")), "🤖")
            st.markdown(f"""
            <div class='task-pill'>
                <div class='dot {dot}'></div>
                <span style='color:#6b7280;font-size:.75rem;font-family:monospace'>#{t["id"]}</span>
                <span style='font-size:.9rem'>{agent_icon}</span>
                <span style='color:#9ca3af;font-size:.75rem'>{t.get("agent_id","?")}{elapsed}</span>
                <span style='flex:1;color:#e2e8f0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{t["prompt"][:100]}</span>
                <span style='color:{"#22c55e" if s=="completed" else "#ef4444" if s in ("failed","timeout") else "#f59e0b"};font-size:.72rem;font-weight:700;white-space:nowrap'>{s.upper()}</span>
            </div>""", unsafe_allow_html=True)
            if t.get("result") and s=="completed":
                with st.expander("View result"):
                    ans = t["result"].get("answer","") if isinstance(t.get("result"),dict) else str(t.get("result",""))
                    st.markdown(f"<div style='color:#e2e8f0;font-size:.87rem;white-space:pre-wrap;line-height:1.6'>{ans[:4000]}</div>", unsafe_allow_html=True)
    elif not isinstance(tasks, list):
        st.error("Could not load tasks")
    else:
        st.markdown("<div style='color:#4b5563;padding:32px;text-align:center'>No tasks yet. Queue one above.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── AGENTS ────────────────────────────────────────────────────────────────────
elif page == "agents":
    st.markdown("<div style='padding:20px 24px'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>🤖 <span>Agent Directory</span></div>", unsafe_allow_html=True)
    stat = get("/api/status")
    c1,c2,c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><div class='metric-val'>{stat.get('agents',11)}</div><div class='metric-lbl'>Agents</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><div class='metric-val'>{stat.get('tasks_running',0)}</div><div class='metric-lbl'>Running</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><div class='metric-val'>{stat.get('tasks_total',0)}</div><div class='metric-lbl'>Total Tasks</div></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    agents = get("/agents")
    if isinstance(agents, list):
        cols = st.columns(4)
        for i, a in enumerate(agents):
            with cols[i % 4]:
                st.markdown(f"""
                <div class='agent-card'>
                    <div style='font-size:1.8rem;margin-bottom:8px'>{a.get("icon","🤖")}</div>
                    <div style='font-weight:700;color:#e2e8f0;font-size:.9rem'>{a.get("name","?")}</div>
                    <div style='color:#6b7280;font-size:.75rem;margin-top:4px;line-height:1.4'>{a.get("role","")[:70]}</div>
                </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── MODELS ────────────────────────────────────────────────────────────────────
elif page == "models":
    st.markdown("<div style='padding:20px 24px'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>🧠 <span>LLM Models</span></div>", unsafe_allow_html=True)
    m = get("/models")
    ol = m.get("ollama",{})
    ol_ok = ol.get("available", False)
    st.markdown(f"""
    <div class='card'>
        <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:12px'>
            <div style='display:flex;align-items:center;gap:10px'>
                <span style='font-size:1.5rem'>🦙</span>
                <div>
                    <div style='font-weight:700;color:#e2e8f0'>Ollama — Local LLM (Free)</div>
                    <div style='font-size:.75rem;color:#6b7280'>{ol.get("base_url","")}</div>
                </div>
            </div>
            <span class='badge {"ok" if ol_ok else "warn"}'>{"● Running" if ol_ok else "● Offline"}</span>
        </div>
        <div style='display:flex;gap:8px;flex-wrap:wrap'>
            {("".join(f"<span style='background:#1e1e3a;color:#a78bfa;border-radius:99px;padding:3px 12px;font-size:.75rem;font-weight:600'>{mod}</span>" for mod in ol.get("models",[])[:8])) or
            "<span style='color:#6b7280;font-size:.82rem'>No models installed. Run: <code style=background:#1e1e3a;padding:2px 8px;border-radius:4px>ollama pull qwen2.5</code></span>"}
        </div>
        {f"<div style='margin-top:10px;color:#6b7280;font-size:.78rem'>Best model: {ol.get('best','?')} · Best coder: {ol.get('best_coder','?')}</div>" if ol_ok else ""}
    </div>""", unsafe_allow_html=True)

    if not ol_ok:
        st.info("💡 **Start Ollama:** `docker compose up -d ollama` then `docker compose exec ollama ollama pull qwen2.5`")

    cloud = m.get("cloud_enabled",{})
    if cloud:
        st.markdown("<div style='font-weight:700;color:#e2e8f0;margin:16px 0 8px'>☁️ Cloud Providers</div>", unsafe_allow_html=True)
        for k in cloud:
            st.markdown(f"<div class='task-pill'><div class='dot ok'></div><span style='color:#e2e8f0'>{k}</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='card' style='border-color:#1e1e3a'>
            <div style='color:#6b7280;font-size:.85rem'>
            ☁️ <strong style='color:#e2e8f0'>Cloud Providers</strong> — all optional. Add to .env:<br>
            <code style='color:#a78bfa'>OPENAI_API_KEY</code> · <code style='color:#a78bfa'>GROQ_API_KEY</code> (free tier) ·
            <code style='color:#a78bfa'>GEMINI_API_KEY</code> · <code style='color:#a78bfa'>XAI_API_KEY</code>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    mn = st.selectbox("Quick pull command", ["qwen2.5","qwen2.5-coder","llama3.2","mistral","phi3","gemma2","codellama","tinyllama"])
    st.code(f"docker compose exec ollama ollama pull {mn}", language="bash")
    st.markdown("</div>", unsafe_allow_html=True)

# ── MEMORY ────────────────────────────────────────────────────────────────────
elif page == "memory":
    st.markdown("<div style='padding:20px 24px'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>🗄️ <span>Memory</span></div>", unsafe_allow_html=True)
    s = get("/api/memory")
    c1,c2,c3,c4 = st.columns(4)
    for col, val, lbl in [(c1,s.get("events",0),"Events"),(c2,s.get("outcomes",0),"Outcomes"),(c3,s.get("conversations",0),"Conversations"),(c4,"✅" if s.get("redis") else "SQLite","Storage")]:
        col.markdown(f"<div class='metric-card'><div class='metric-val'>{val}</div><div class='metric-lbl'>{lbl}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#4b5563;font-size:.75rem;margin:8px 0'>{s.get('db_path','')}</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Recent Events", "Outcomes"])
    with tab1:
        if st.button("🔄 Refresh", key="mem_refresh"): st.rerun()
        evts = get("/memory/events?limit=30")
        if isinstance(evts, list):
            for e in evts:
                ts = datetime.fromtimestamp(e.get("created",0)).strftime("%H:%M:%S")
                kind = e.get("kind","")
                is_ok = any(x in kind for x in ("ok","start","complet","creat"))
                is_err = any(x in kind for x in ("error","fail"))
                color = "#22c55e" if is_ok else "#ef4444" if is_err else "#6b7280"
                p = str(e.get("payload",""))[:120]
                st.markdown(f"""
                <div style='display:flex;gap:12px;padding:7px 0;border-bottom:1px solid #111130;font-size:.8rem'>
                    <span style='color:#4b5563;font-family:monospace;white-space:nowrap'>{ts}</span>
                    <span style='color:{color};font-weight:600;min-width:130px;white-space:nowrap'>{kind}</span>
                    <span style='color:#6b7280;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{p}</span>
                </div>""", unsafe_allow_html=True)
    with tab2:
        outcomes = get("/memory/outcomes?limit=20")
        if isinstance(outcomes, list) and outcomes:
            for o in outcomes:
                score = o.get("score",0) or 0
                color = "#22c55e" if score > 0.7 else "#f59e0b" if score > 0.4 else "#ef4444"
                st.markdown(f"""
                <div class='task-pill'>
                    <span style='color:#9ca3af'>{o.get("agent","?")}</span>
                    <span style='flex:1;color:#e2e8f0'>{str(o.get("goal",""))[:80]}</span>
                    <span style='color:{color};font-weight:700'>{score:.2f}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#4b5563;padding:20px;text-align:center'>No outcomes yet</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── REWARDS ───────────────────────────────────────────────────────────────────
elif page == "rewards":
    st.markdown("<div style='padding:20px 24px'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>💰 <span>Reward Discovery</span></div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6b7280;font-size:.83rem;margin-bottom:16px'>Legal opportunities: bug bounties · hackathons · grants · freelance</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2,2,1])
    eff = col1.selectbox("Effort", ["all","low","medium","high"])
    typ = col2.selectbox("Type", ["all","bug_bounty","hackathon","grant","freelance","bounty"])
    if col3.button("🔄 Refresh"): st.rerun()

    data = get("/rewards")
    items = data.get("opportunities",[]) if isinstance(data,dict) else []
    filtered = [o for o in items if (eff=="all" or o.get("effort")==eff) and (typ=="all" or o.get("type")==typ)]

    if filtered:
        cols = st.columns(2)
        for i, o in enumerate(filtered):
            with cols[i % 2]:
                type_colors = {"bug_bounty":"#1e1e3a","hackathon":"#1a2e1a","grant":"#1a1e2e","freelance":"#1e1a2e","bounty":"#1e1e3a"}
                type_txt_colors = {"bug_bounty":"#a78bfa","hackathon":"#22c55e","grant":"#60a5fa","freelance":"#f59e0b","bounty":"#a78bfa"}
                tc = type_colors.get(o.get("type",""), "#1e1e3a")
                ttc = type_txt_colors.get(o.get("type",""), "#a78bfa")
                st.markdown(f"""
                <div class='reward-card'>
                    <div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px'>
                        <span style='background:{tc};color:{ttc};border-radius:99px;padding:3px 10px;font-size:.72rem;font-weight:700'>{o.get("type","?")}</span>
                        <span style='color:#22c55e;font-weight:800;font-size:.9rem'>{o.get("payout","?")}</span>
                    </div>
                    <div style='font-weight:700;color:#e2e8f0;font-size:.92rem;margin-bottom:4px'>{o.get("title","")}</div>
                    <div style='color:#6b7280;font-size:.78rem;line-height:1.5;margin-bottom:8px'>{o.get("description","")[:100]}</div>
                    <a href='{o.get("url","#")}' target='_blank' style='color:#7c3aed;font-size:.75rem;text-decoration:none'>→ {o.get("url","")[:55]}</a>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("No opportunities match the selected filters.")
    st.markdown("</div>", unsafe_allow_html=True)

# ── BUG BOUNTY ────────────────────────────────────────────────────────────────
elif page == "bounty":
    st.markdown("<div style='padding:20px 24px'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>🎯 <span>Bug Bounty Planner</span></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#1a0808;border:1px solid #7f1d1d;border-radius:10px;padding:10px 14px;color:#fca5a5;font-size:.82rem;margin-bottom:16px'>
    ⚠️ <strong>Authorized programs only.</strong> Only test targets you have explicit written permission to test. Responsible disclosure required.
    </div>""", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 New Plan", "📁 My Plans"])
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            prog = st.text_input("Program name", "HackerOne Example Program")
        with col2:
            scope = st.text_input("Scope", "*.example.com")
        auth = st.text_input("Authorization statement", "I have written permission from example.com to test their bug bounty program.")
        if st.button("Generate OWASP Checklist ➤", use_container_width=True, type="primary"):
            if auth.strip():
                r = post("/bounty/plan", {"program": prog, "scope": scope, "authorization": auth})
                if r.get("id"):
                    st.success(f"✅ Plan `{r['id']}` created — {len(r.get('checks',[]))} OWASP checks")
                    for c in r.get("checks",[]):
                        st.markdown(f"<div class='task-pill'><div class='dot q'></div><span style='color:#e2e8f0'>{c['name']}</span></div>", unsafe_allow_html=True)
                else:
                    st.error(str(r))
            else:
                st.warning("Authorization statement required")

    with tab2:
        if st.button("🔄 Refresh", key="bounty_refresh"): st.rerun()
        plans = get("/bounty/plans")
        if isinstance(plans, list) and plans:
            for plan in plans:
                found = sum(1 for c in plan.get("checks",[]) if c["status"]=="found")
                total = len(plan.get("checks",[]))
                pending = sum(1 for c in plan.get("checks",[]) if c["status"]=="pending")
                st.markdown(f"""
                <div class='card'>
                    <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px'>
                        <div style='font-weight:700;color:#e2e8f0'>{plan.get("program","?")}</div>
                        <span class='badge ok'>ID: {plan.get("id","?")}</span>
                    </div>
                    <div style='color:#6b7280;font-size:.8rem'>{total} checks · {pending} pending · {found} findings · {plan.get("scope","")}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#4b5563;padding:20px;text-align:center'>No plans yet</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── BROWSER ───────────────────────────────────────────────────────────────────
elif page == "browser":
    st.markdown("<div style='padding:20px 24px'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>🌐 <span>Browser Agent</span></div>", unsafe_allow_html=True)

    bs = get("/api/browser/status", 6)
    eng = bs.get("engine","unknown")
    avail = bs.get("available",False)
    mode = bs.get("mode","")
    features = bs.get("features",[])
    color = "#22c55e" if avail else "#ef4444"

    st.markdown(f"""
    <div class='card' style='border-color:{color}33'>
        <div style='display:flex;align-items:center;justify-content:space-between'>
            <div>
                <span style='color:{color};font-weight:700;font-size:.95rem'>● {eng.upper()} engine — {mode} mode</span>
                <div style='color:#6b7280;font-size:.78rem;margin-top:4px'>{" · ".join(features)}</div>
            </div>
            <span class='badge {"ok" if avail else "err"}'>{"OPERATIONAL" if avail else "OFFLINE"}</span>
        </div>
        {("<div style='color:#f59e0b;font-size:.75rem;margin-top:8px'>ℹ️ " + bs.get("note","") + "</div>") if bs.get("note") else ""}
    </div>""", unsafe_allow_html=True)

    url = st.text_input("URL", "https://example.com")
    t1, t2, t3, t4 = st.tabs(["📄 Fetch", "📝 Extract", "🔍 Summarize", "📊 Structured"])

    with t1:
        if st.button("🌐 Fetch Page", use_container_width=True, type="primary"):
            with st.spinner("Fetching…"):
                r = post("/browser/fetch", {"url": url}, 35)
            if r.get("ok"):
                st.success(f"✅ {r.get('engine','?').upper()} · HTTP {r.get('status_code','?')} · {r.get('title','')[:80]}")
                if r.get("screenshot_b64"):
                    import base64
                    st.image(base64.b64decode(r["screenshot_b64"]), caption="Screenshot", use_column_width=True)
                st.text_area("Content", r.get("text","")[:3000], height=200)
            else:
                st.error(r.get("error","Failed"))

    with t2:
        if st.button("📝 Extract Text", use_container_width=True, type="primary"):
            with st.spinner("Extracting…"):
                r = post("/browser/extract", {"url": url}, 30)
            if r.get("ok"):
                st.success(f"✅ {r.get('title','')[:80]}")
                st.text_area("Text", r.get("text","")[:5000], height=300)
                if r.get("links"):
                    st.markdown("**Links found:**")
                    for lnk in r["links"][:10]:
                        href = lnk.get("href","")
                        txt = lnk.get("text","?")[:50]
                        st.markdown(f"- [{txt}]({href})" if href.startswith("http") else f"- {txt} ({href})")
            else:
                st.error(r.get("error","Failed"))

    with t3:
        if st.button("🔍 Summarize (AI)", use_container_width=True, type="primary"):
            with st.spinner("Summarizing with LLM…"):
                r = post("/browser/summarize", {"url": url}, 60)
            if r.get("ok"):
                st.success(f"✅ {r.get('title','')[:80]}")
                st.markdown(r.get("summary","No summary"))
            else:
                st.error(r.get("error","Failed"))

    with t4:
        schema_inp = st.text_area("CSS Schema (JSON)", '{"title":"h1","description":"p","price":".price"}', height=80)
        if st.button("📊 Extract Structured", use_container_width=True, type="primary"):
            try:
                schema = json.loads(schema_inp)
                with st.spinner("Extracting…"):
                    r = post("/browser/structured", {"url": url, "schema": schema}, 30)
                if r.get("ok"):
                    st.json(r.get("data",{}))
                else:
                    st.error(r.get("error","Failed"))
            except Exception as e:
                st.error(f"Invalid JSON: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# ── TOOLS ─────────────────────────────────────────────────────────────────────
elif page == "tools":
    st.markdown("<div style='padding:20px 24px'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>🔧 <span>Tools</span></div>", unsafe_allow_html=True)
    tools = get("/api/tools")
    skill_list = get("/skills")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div style='font-weight:700;color:#e2e8f0;margin-bottom:12px'>🔧 Tools Registry</div>", unsafe_allow_html=True)
        tool_icons = {"web":"🔍","http":"🌐","code":"💻","files":"📁","stripe":"💳","email":"📧","telegram":"✈️","apollo":"👥","hunter":"🎯","mastodon":"🐘","buffer":"📅","usdc":"💵","hackerone":"🐛"}
        if isinstance(tools, list):
            for t in tools:
                icon = next((v for k,v in tool_icons.items() if k in t.get("id","")), "⚙️")
                st.markdown(f"<div class='task-pill'><span style='font-size:1rem'>{icon}</span><span style='color:#e2e8f0;font-weight:600'>{t.get('name','?')}</span><span style='color:#6b7280;font-size:.75rem'>{t.get('id','')}</span></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='font-weight:700;color:#e2e8f0;margin-bottom:12px'>⚡ Skills Registry</div>", unsafe_allow_html=True)
        if isinstance(skill_list, list):
            for s in skill_list:
                st.markdown(f"<div class='task-pill'><span style='color:#a78bfa;font-size:.8rem'>▸</span><span style='color:#e2e8f0;font-weight:600'>{s.get('name',s.get('id','?'))}</span><span style='color:#6b7280;font-size:.75rem'>{s.get('description',s.get('desc',''))[:60]}</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── ARTIFACTS ─────────────────────────────────────────────────────────────────
elif page == "artifacts":
    st.markdown("<div style='padding:20px 24px'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>📦 <span>Artifacts</span></div>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📁 Library", "✏️ Create"])
    with tab1:
        if st.button("🔄 Refresh", key="art_refresh"): st.rerun()
        arts = get("/api/artifacts")
        items = arts.get("artifacts",[]) if isinstance(arts,dict) else []
        if items:
            for a in items:
                size_kb = a.get("size_bytes",0)/1024
                ts = datetime.fromtimestamp(a.get("modified",0)).strftime("%Y-%m-%d %H:%M")
                fmt_colors = {"md":"#a78bfa","html":"#60a5fa","csv":"#22c55e","xlsx":"#f59e0b"}
                fc = fmt_colors.get(a.get("format",""), "#6b7280")
                st.markdown(f"""
                <div class='task-pill'>
                    <span style='color:{fc};font-weight:700;font-size:.75rem;min-width:35px'>{a.get("format","?").upper()}</span>
                    <span style='color:#e2e8f0;flex:1'>{a.get("name","?")}</span>
                    <span style='color:#6b7280;font-size:.72rem'>{size_kb:.1f} KB</span>
                    <span style='color:#4b5563;font-size:.7rem'>{ts}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#4b5563;padding:32px;text-align:center'>No artifacts yet</div>", unsafe_allow_html=True)
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Title", "My Artifact")
            fmt = st.selectbox("Format", ["markdown","html","csv"])
        with col2:
            st.write("")
            st.markdown("<div style='color:#6b7280;font-size:.8rem;padding-top:12px'>Artifacts are saved to data/artifacts/</div>", unsafe_allow_html=True)
        content = st.text_area("Content", "# Hello\nThis is my artifact.", height=200)
        if st.button("💾 Create Artifact", use_container_width=True, type="primary"):
            r = post("/artifact/create", {"title": title, "content": content, "format": fmt})
            if r.get("type") or r.get("path"):
                fname = (r.get("path") or "").split("/")[-1] or title
                st.success(f"✅ Created: {fname}")
                st.rerun()
            else:
                st.error(str(r.get("error", r)))
    st.markdown("</div>", unsafe_allow_html=True)

# ── LOGS ──────────────────────────────────────────────────────────────────────
elif page == "logs":
    st.markdown("<div style='padding:20px 24px'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>📋 <span>System Logs</span></div>", unsafe_allow_html=True)
    col_a, col_b = st.columns([5,1])
    with col_b:
        if st.button("🔄 Refresh"): st.rerun()
    evts = get("/logs?limit=60")
    if isinstance(evts, list):
        for e in reversed(evts):
            ts = datetime.fromtimestamp(e.get("created",0)).strftime("%H:%M:%S")
            kind = e.get("kind","")
            is_ok = any(x in kind for x in ("ok","start","complet","creat"))
            is_err = any(x in kind for x in ("error","fail"))
            color = "#22c55e" if is_ok else "#ef4444" if is_err else "#6b7280"
            payload = str(e.get("payload",""))[:180]
            st.markdown(f"""
            <div style='display:flex;gap:12px;align-items:flex-start;padding:7px 0;border-bottom:1px solid #111130;font-size:.8rem'>
                <span style='color:#4b5563;font-family:monospace;white-space:nowrap;min-width:60px'>{ts}</span>
                <span style='color:{color};font-weight:700;white-space:nowrap;min-width:130px'>{kind}</span>
                <span style='color:#6b7280;word-break:break-word'>{payload}</span>
            </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── SETTINGS ──────────────────────────────────────────────────────────────────
elif page == "settings":
    st.markdown("<div style='padding:20px 24px'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>⚙️ <span>Settings</span></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Diagnostics", "⚙️ Config", "👤 Profile"])

    with tab1:
        if st.button("🔄 Refresh", key="diag_refresh"): st.rerun()
        startup = get("/startup")
        summary = startup.get("_summary",{})
        ok_c = summary.get("ok",0); tot = summary.get("total",0)
        bar_pct = int((ok_c/tot)*100) if tot else 0
        bar_color = "#22c55e" if ok_c==tot else "#f59e0b" if ok_c/max(tot,1)>0.6 else "#ef4444"
        st.markdown(f"""
        <div style='background:#0f0f1e;border:1px solid #1e1e3a;border-radius:12px;padding:16px;margin-bottom:16px'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px'>
                <span style='color:#e2e8f0;font-weight:700'>System Health</span>
                <span style='color:{bar_color};font-weight:700'>{ok_c}/{tot} OK</span>
            </div>
            <div style='background:#1e1e3a;border-radius:99px;height:6px'>
                <div style='background:{bar_color};width:{bar_pct}%;height:6px;border-radius:99px;transition:.3s'></div>
            </div>
        </div>""", unsafe_allow_html=True)

        icons_map = {"python":"🐍","memory_db":"🗄️","ollama":"🦙","langgraph":"🔗","browser":"🌐","redis":"⚡","telegram":"✈️","llm":"🧠"}
        for key, val in startup.items():
            if key == "_summary": continue
            chk_ok = val.get("ok",False); deg = val.get("degraded",False)
            sc = "#22c55e" if chk_ok else "#f59e0b" if deg else "#ef4444"
            st_txt = "OK" if chk_ok else "Degraded" if deg else "Offline"
            note = val.get("note") or val.get("error") or val.get("version") or val.get("best") or ""
            icon = icons_map.get(key,"⚙️")
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:12px;padding:11px 14px;background:#0f0f1e;border:1px solid #1e1e3a;border-radius:10px;margin:5px 0'>
                <span style='font-size:1.1rem'>{icon}</span>
                <span style='color:#e2e8f0;font-weight:600;flex:1'>{key}</span>
                <span style='color:#6b7280;font-size:.75rem;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{str(note)[:60]}</span>
                <span class='badge {"ok" if chk_ok else "warn" if deg else "err"}'>{st_txt}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown(f"<div style='color:#4b5563;font-size:.72rem;margin-top:8px'>API: {API}</div>", unsafe_allow_html=True)

    with tab2:
        cfg = get("/settings")
        if isinstance(cfg, dict):
            col1, col2 = st.columns(2)
            with col1:
                opts = ["auto","qwen2.5","qwen2.5-coder","llama3.2","mistral","phi3"]
                cur = cfg.get("ollama_model","auto")
                idx = opts.index(cur) if cur in opts else 0
                ollama_model = st.selectbox("Default Ollama Model", opts, index=idx)
                strict = st.toggle("Strict Guardrails", cfg.get("guardrails_strict",True))
            with col2:
                max_tasks = st.slider("Max Parallel Tasks", 1, 16, cfg.get("max_parallel_tasks",4))
            if st.button("💾 Save Config", use_container_width=True, type="primary"):
                r = post("/settings", {"ollama_model": ollama_model, "max_parallel_tasks": max_tasks, "guardrails_strict": strict})
                st.success("✅ Config saved")

    with tab3:
        user = get("/user")
        if isinstance(user, dict):
            st.markdown(f"""
            <div class='card'>
                <div style='font-weight:700;color:#e2e8f0;font-size:.95rem;margin-bottom:8px'>👤 {user.get("display_name","operator")}</div>
                <div style='color:#6b7280;font-size:.8rem'>ID: {user.get("user_id","?")} · Network: {"✅" if user.get("network_enabled") else "🚫"}</div>
            </div>""", unsafe_allow_html=True)
            dn = st.text_input("Display Name", user.get("display_name","operator"))
            net = st.toggle("Network Access", user.get("network_enabled",True))
            if st.button("💾 Save Profile", use_container_width=True, type="primary"):
                post("/user", {"display_name": dn, "network_enabled": net})
                st.success("✅ Profile saved"); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
