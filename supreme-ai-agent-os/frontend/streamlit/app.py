import json
import requests
import streamlit as st

API = st.secrets.get("SUPREME_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Supreme AI Agent OS", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

if "page" not in st.session_state:
    st.session_state.page = "Command"
if "messages" not in st.session_state:
    st.session_state.messages = []

def get(path):
    try:
        return requests.get(API + path, timeout=10).json()
    except Exception as e:
        return {"error": str(e)}

def post(path, payload, timeout=120):
    try:
        return requests.post(API + path, json=payload, timeout=timeout).json()
    except Exception as e:
        return {"error": str(e)}

st.markdown("""
<style>
header[data-testid="stHeader"], section[data-testid="stSidebar"] {display:none!important}
.block-container {max-width:1120px!important; padding-top:1.2rem!important}
.stApp {background:#f4f4f2;color:#242424}
h1,h2,h3,p,label,span,div {color:#242424}
.logo {font-family:Georgia,serif;font-size:2.25rem;font-weight:900;text-align:center}
.card {background:white;border-radius:28px;padding:24px;margin:16px 0;box-shadow:0 10px 30px rgba(0,0,0,.075)}
.item {background:white;border-radius:22px;padding:18px;margin:12px 0;box-shadow:0 6px 20px rgba(0,0,0,.055)}
.chat {background:white;border-radius:22px;padding:18px;margin:12px 0;white-space:pre-wrap;box-shadow:0 6px 20px rgba(0,0,0,.055)}
.term {background:#111827;color:#d1fae5;border-radius:18px;padding:16px;font-family:monospace;white-space:pre-wrap}
.ok {color:#16a34a;font-weight:900}.muted{color:#737373}.lock{color:#999;font-weight:800}
.stButton button {background:#1d1d1f!important;color:white!important;border:0!important;border-radius:999px!important;min-height:44px;font-weight:900!important}
textarea,input {background:white!important;color:#242424!important;border:1px solid #ddd!important;border-radius:18px!important}
</style>
""", unsafe_allow_html=True)

pages = ["Command", "Agents", "Skills", "Connectors", "Data Lab", "Terminal", "Artifacts", "Library", "Manual"]
st.markdown("<div class='logo'>supreme</div>", unsafe_allow_html=True)
cols = st.columns(len(pages))
for i, p in enumerate(pages):
    if cols[i].button(p, use_container_width=True):
        st.session_state.page = p
        st.rerun()

health = get("/health")
st.markdown(f"<div class='card'><span class='ok'>● {'Backend online' if health.get('status') == 'ok' else 'Backend issue'}</span> <span class='muted'>API: {API}</span></div>", unsafe_allow_html=True)

page = st.session_state.page

if page == "Command":
    st.header("Command Center")
    agents = get("/agents")
    agent_options = {a["name"]: a["id"] for a in agents if isinstance(a, dict)} if isinstance(agents, list) else {"Executive Agent": "executive"}
    selected_name = st.selectbox("Agent", list(agent_options.keys()))
    prompt = st.text_area("Task", height=140, placeholder="Ask the agent to plan, create, inspect, debug, research, or prepare commands.")
    raw = st.text_area("Optional raw data/logs/env", height=100)
    upload = st.file_uploader("Optional file", type=["txt","csv","json","log","md","env"])
    file_text = upload.read().decode("utf-8", errors="ignore") if upload else ""
    if st.button("Run Agent", use_container_width=True):
        res = post("/agent/run", {"prompt": prompt, "raw_data": raw, "file_text": file_text, "agent_id": agent_options[selected_name]}, 140)
        st.session_state.messages.append(("You", prompt or "Data task"))
        st.session_state.messages.append((res.get("provider", "Agent"), res.get("answer", json.dumps(res, indent=2))))
        st.rerun()
    for who, msg in st.session_state.messages[-10:]:
        st.markdown(f"<div class='chat'><b>{who}</b><br>{msg}</div>", unsafe_allow_html=True)

elif page == "Agents":
    st.header("Agent Directory")
    for a in get("/agents"):
        st.markdown(f"<div class='item'><h2>{a.get('name')}</h2><p>{a.get('role')}</p></div>", unsafe_allow_html=True)

elif page == "Skills":
    st.header("Skills")
    for s in get("/skills"):
        st.markdown(f"<div class='item'><h2>{s.get('name')}</h2><p>{s.get('desc')}</p></div>", unsafe_allow_html=True)

elif page == "Connectors":
    st.header("Connectors")
    for c in get("/connectors"):
        status = "✅ Enabled" if c.get("enabled") else "🔒 Add required key in .env"
        st.markdown(f"<div class='item'><h2>{c.get('name')}</h2><p>{status}</p></div>", unsafe_allow_html=True)

elif page == "Data Lab":
    st.header("Data Lab")
    d = st.text_area("Paste raw data", height=240)
    f = st.file_uploader("Upload data", type=["txt","csv","json","log","md","env"])
    if f:
        d = f.read().decode("utf-8", errors="ignore")
    if st.button("Analyze", use_container_width=True):
        kind = "Text"
        try:
            json.loads(d)
            kind = "JSON"
        except Exception:
            pass
        st.markdown(f"<div class='card'><h3>{kind}</h3><p>Characters: {len(d)}</p><p>Lines: {d.count(chr(10))+1 if d else 0}</p></div>", unsafe_allow_html=True)
        st.text_area("Preview", d[:6000], height=240)

elif page == "Terminal":
    st.header("Remote EC2 Terminal")
    st.warning("Runs real backend commands. Destructive commands are blocked.")
    cmd = st.text_area("Command", height=140, placeholder="df -h && free -h && uptime")
    if st.button("Execute", use_container_width=True):
        st.session_state.terminal = post("/system/exec", {"command": cmd, "timeout": 120}, 140)
    if "terminal" in st.session_state:
        o = st.session_state.terminal
        st.markdown(f"<div class='term'>$ {o.get('command','')}\n\nSTDOUT:\n{o.get('stdout','')}\n\nSTDERR:\n{o.get('stderr','')}\n\nExit: {o.get('returncode')}</div>", unsafe_allow_html=True)

elif page == "Artifacts":
    st.header("Artifact Factory")
    title = st.text_input("Title", "Untitled")
    fmt = st.selectbox("Format", ["markdown", "html", "xlsx", "csv"])
    content = st.text_area("Content / CSV data", height=200)
    if st.button("Create Artifact", use_container_width=True):
        st.json(post("/artifact/create", {"title": title, "format": fmt, "content": content}))

elif page == "Library":
    st.header("Library")
    state = get("/state")
    title = st.text_input("Title")
    typ = st.selectbox("Type", ["Document","Website","Spreadsheet","Note","Other"])
    content = st.text_area("Content", height=160)
    if st.button("Save", use_container_width=True):
        st.json(post("/library/add", {"title": title or "Untitled", "type": typ, "content": content}))
    for item in state.get("library", []):
        st.markdown(f"<div class='item'><h2>{item.get('title')}</h2><p>{item.get('type')}</p><p>{item.get('content','')[:500]}</p></div>", unsafe_allow_html=True)

elif page == "Manual":
    st.header("Manual")
    st.markdown("""
### Operating Model
1. Use **Command** for agent tasks.
2. Use **Terminal** for approved backend execution.
3. Use **Artifacts** for Markdown, HTML, CSV, XLSX.
4. Add keys to `.env`; capability-gated modules activate automatically.
5. Use GitHub to track every change.

### Provider Priority
Grok/XAI → Gemini → Bedrock → OpenAI → Groq/OpenRouter fallback.

### GitHub Update Flow
Run:
```bash
bash scripts/git_push_update.sh "your change summary"
```
""")
