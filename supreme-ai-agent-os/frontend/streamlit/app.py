"""
Supreme AI Agent OS - Streamlit Frontend
Modern, responsive UI with engaging visuals and smooth interactions
"""
import json
import requests
import streamlit as st
from datetime import datetime
import time

# Configuration
API = st.secrets.get("SUPREME_API_URL", "http://127.0.0.1:8000")
REFRESH_INTERVAL = 30

# Page Config - Must be first
st.set_page_config(
    page_title="Supreme AI Agent OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# Session State Initialization
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# Utility Functions
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

# Enhanced CSS Styling
st.markdown("""
<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #2d1b69 100%);
    color: #e4e4e7;
}

[data-testid="stHeader"], [data-testid="stSidebar"] { display: none !important; }

.block-container {
    max-width: 1400px !important;
    padding: 2rem 1.5rem !important;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    color: #f1f5f9 !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px;
}

h1 { font-size: 3.5rem !important; margin-bottom: 0.5rem !important; }
h2 { font-size: 2rem !important; margin-bottom: 1rem !important; }
h3 { font-size: 1.5rem !important; margin-bottom: 0.75rem !important; }

p, span, label, div { color: #e4e4e7 !important; }

/* Logo */
.logo {
    font-family: "Georgia", serif;
    font-size: 3.5rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(135deg, #60a5fa, #a78bfa, #f87171);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -2px;
    margin-bottom: 2rem;
    text-shadow: 0 10px 30px rgba(96, 165, 250, 0.3);
}

/* Cards & Containers */
.card {
    background: rgba(30, 27, 75, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.card:hover {
    background: rgba(30, 27, 75, 0.8);
    border-color: rgba(148, 163, 184, 0.4);
    box-shadow: 0 25px 60px rgba(96, 165, 250, 0.2);
    transform: translateY(-2px);
}

.item {
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(100, 116, 139, 0.2);
    border-radius: 12px;
    padding: 16px;
    margin: 12px 0;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(8px);
    transition: all 0.2s ease;
}

.item:hover {
    background: rgba(30, 27, 75, 0.6);
    border-color: rgba(148, 163, 184, 0.3);
    transform: translateX(4px);
}

.chat {
    background: rgba(15, 23, 42, 0.4);
    border-left: 4px solid #60a5fa;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.term {
    background: #0f172a;
    color: #22c55e;
    border-radius: 12px;
    padding: 16px;
    font-family: "Fira Code", monospace;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 0.85rem;
    line-height: 1.5;
    border: 1px solid rgba(34, 197, 94, 0.2);
}

/* Status Indicators */
.status-ok { 
    color: #22c55e !important; 
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.status-error { 
    color: #ef4444 !important; 
    font-weight: 700;
}

.status-warning { 
    color: #f59e0b !important; 
    font-weight: 700;
}

.status-info { 
    color: #60a5fa !important; 
    font-weight: 700;
}

.muted { color: #94a3b8 !important; }
.lock { color: #64748b !important; font-weight: 600; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    min-height: 44px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 15px 30px rgba(59, 130, 246, 0.4) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* Inputs */
input, textarea {
    background: rgba(15, 23, 42, 0.8) !important;
    color: #e4e4e7 !important;
    border: 1px solid rgba(148, 163, 184, 0.2) !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    transition: all 0.3s ease !important;
    font-size: 1rem !important;
}

input:focus, textarea:focus {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.1) !important;
    background: rgba(15, 23, 42, 0.95) !important;
}

/* Selectbox */
[data-baseweb="select"] {
    background: rgba(15, 23, 42, 0.8) !important;
}

/* Tabs & Navigation */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(30, 27, 75, 0.5) !important;
    border-radius: 8px !important;
    color: #cbd5e1 !important;
    padding: 10px 20px !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    color: white !important;
}

/* Success/Error Messages */
.stSuccess {
    background: rgba(34, 197, 94, 0.1) !important;
    border: 1px solid #22c55e !important;
    border-radius: 8px !important;
}

.stError {
    background: rgba(239, 68, 68, 0.1) !important;
    border: 1px solid #ef4444 !important;
    border-radius: 8px !important;
}

.stWarning {
    background: rgba(245, 158, 11, 0.1) !important;
    border: 1px solid #f59e0b !important;
    border-radius: 8px !important;
}

.stInfo {
    background: rgba(96, 165, 250, 0.1) !important;
    border: 1px solid #60a5fa !important;
    border-radius: 8px !important;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.card, .item { animation: fadeIn 0.4s ease-out; }

/* Responsive */
@media (max-width: 768px) {
    .logo { font-size: 2rem !important; }
    h1 { font-size: 2rem !important; }
    h2 { font-size: 1.5rem !important; }
    .block-container { padding: 1rem !important; }
}
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown("<div class='logo'>⚡ supreme</div>", unsafe_allow_html=True)

# Navigation Buttons
pages = ["Dashboard", "Command", "Agents", "Skills", "Connectors", "Lab", "Terminal", "Artifacts", "Library", "Settings"]
cols = st.columns(len(pages))
for i, p in enumerate(pages):
    if cols[i].button(p, use_container_width=True, key=f"nav_{p}"):
        st.session_state.page = p
        st.rerun()

# Status Bar
col1, col2, col3 = st.columns(3)
health = get("/health")
status_text = "🟢 Backend Online" if health.get("status") == "ok" else "🔴 Backend Issue"

with col1:
    if health.get("status") == "ok":
        st.markdown(f"<div class='card'><span class='status-ok'>{status_text}</span></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='card'><span class='status-error'>{status_text}</span></div>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<div class='card'><span class='status-info'>⏱ {datetime.now().strftime('%H:%M:%S')}</span></div>", unsafe_allow_html=True)

with col3:
    st.markdown(f"<div class='card'><span class='muted'>API: {API}</span></div>", unsafe_allow_html=True)

st.divider()

# Page Content
page = st.session_state.page

if page == "Dashboard":
    st.markdown("<h2>🎯 Dashboard</h2>", unsafe_allow_html=True)
    
    # System Status
    col1, col2, col3, col4 = st.columns(4)
    
    capabilities = get("/capabilities")
    total_llms = len([x for x in capabilities.get("llm", {}).values() if x])
    total_connectors = len([x for x in capabilities.get("connectors", {}).values() if x])
    
    with col1:
        st.markdown(f"""
        <div class='card'>
            <h3>📊 Models</h3>
            <p style='font-size: 2rem; color: #60a5fa;'>{total_llms}</p>
            <p class='muted'>LLM Providers Enabled</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='card'>
            <h3>🔗 Connectors</h3>
            <p style='font-size: 2rem; color: #a78bfa;'>{total_connectors}</p>
            <p class='muted'>Integrations Active</p>
        </div>
        """, unsafe_allow_html=True)
    
    agents = get("/agents")
    agent_count = len(agents) if isinstance(agents, list) else 1
    
    with col3:
        st.markdown(f"""
        <div class='card'>
            <h3>🤖 Agents</h3>
            <p style='font-size: 2rem; color: #f87171;'>{agent_count}</p>
            <p class='muted'>Available Agents</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='card'>
            <h3>⚙️ Skills</h3>
            <p style='font-size: 2rem; color: #22c55e;'>{len(get('/skills'))}</p>
            <p class='muted'>Registered Skills</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Quick Start Guide
    st.markdown("""
    <div class='card'>
        <h3>🚀 Quick Start</h3>
        <ol>
            <li><strong>Command:</strong> Send tasks to agents with optional data</li>
            <li><strong>Lab:</strong> Analyze and process your data</li>
            <li><strong>Terminal:</strong> Execute system commands (if enabled)</li>
            <li><strong>Artifacts:</strong> Generate documents, HTML, CSV, XLSX</li>
            <li><strong>Library:</strong> Store and organize your work</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

elif page == "Command":
    st.markdown("<h2>💬 Command Center</h2>", unsafe_allow_html=True)
    
    agents = get("/agents")
    agent_options = {a["name"]: a["id"] for a in agents if isinstance(a, dict)} if isinstance(agents, list) else {"Executive": "executive"}
    
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_name = st.selectbox("🤖 Select Agent", list(agent_options.keys()), key="agent_select")
    
    prompt = st.text_area("📝 Your Task", height=120, placeholder="Ask the agent to plan, create, analyze, debug, or prepare...")
    
    col1, col2 = st.columns(2)
    with col1:
        raw = st.text_area("📊 Optional Data", height=80, placeholder="Paste logs, CSV, JSON, or raw data...")
    with col2:
        upload = st.file_uploader("📄 Or Upload File", type=["txt","csv","json","log","md","env", "py"])
    
    file_text = upload.read().decode("utf-8", errors="ignore") if upload else ""
    
    if st.button("🚀 Execute Agent", use_container_width=True, key="run_agent"):
        with st.spinner("⏳ Agent is working..."):
            res = post("/agent/run", {"prompt": prompt, "raw_data": raw, "file_text": file_text, "agent_id": agent_options[selected_name]}, 140)
            st.session_state.messages.append(("You", prompt or "Data task"))
            st.session_state.messages.append((res.get("provider", "Agent"), res.get("answer", json.dumps(res, indent=2))))
    
    if st.session_state.messages:
        st.divider()
        st.markdown("<h3>💭 Conversation</h3>", unsafe_allow_html=True)
        for who, msg in st.session_state.messages[-10:]:
            if who == "You":
                st.markdown(f"<div class='chat' style='border-left-color: #60a5fa;'><b>👤 You</b><br>{msg[:500]}...</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat' style='border-left-color: #a78bfa;'><b>🤖 {who}</b><br>{msg[:500]}...</div>", unsafe_allow_html=True)

elif page == "Agents":
    st.markdown("<h2>🤖 Agent Directory</h2>", unsafe_allow_html=True)
    agents = get("/agents")
    if agents and not agents.get("error"):
        cols = st.columns(2)
        for i, a in enumerate(agents):
            with cols[i % 2]:
                st.markdown(f"""
                <div class='item'>
                    <h3>👤 {a.get('name', 'Unknown')}</h3>
                    <p><strong>Role:</strong> {a.get('role', 'N/A')}</p>
                    <p class='muted'>{a.get('desc', 'No description')}</p>
                </div>
                """, unsafe_allow_html=True)

elif page == "Skills":
    st.markdown("<h2>⚙️ Skills Registry</h2>", unsafe_allow_html=True)
    skills = get("/skills")
    if skills and not skills.get("error"):
        cols = st.columns(2)
        for i, s in enumerate(skills):
            with cols[i % 2]:
                st.markdown(f"""
                <div class='item'>
                    <h3>🛠 {s.get('name', 'Unknown')}</h3>
                    <p class='muted'>{s.get('desc', 'No description')}</p>
                </div>
                """, unsafe_allow_html=True)

elif page == "Connectors":
    st.markdown("<h2>🔗 Connectors</h2>", unsafe_allow_html=True)
    connectors = get("/connectors")
    if connectors and not connectors.get("error"):
        cols = st.columns(2)
        for i, c in enumerate(connectors):
            with cols[i % 2]:
                status_icon = "✅" if c.get("enabled") else "🔒"
                status_color = "status-ok" if c.get("enabled") else "status-warning"
                st.markdown(f"""
                <div class='item'>
                    <h3>{status_icon} {c.get('name', 'Unknown')}</h3>
                    <p class='{status_color}'>{'Enabled' if c.get('enabled') else 'Add key in .env'}</p>
                </div>
                """, unsafe_allow_html=True)

elif page == "Lab":
    st.markdown("<h2>🔬 Data Lab</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        data = st.text_area("📝 Paste Data", height=200, placeholder="JSON, CSV, text, logs...")
    
    with col2:
        upload = st.file_uploader("📤 Upload File", type=["txt","csv","json","log","md"])
        if upload:
            data = upload.read().decode("utf-8", errors="ignore")
    
    if data and st.button("🔍 Analyze", use_container_width=True):
        kind = "Text"
        try:
            json.loads(data)
            kind = "JSON"
        except:
            pass
        
        st.markdown(f"""
        <div class='card'>
            <h3>📊 Analysis Results</h3>
            <p><strong>Type:</strong> {kind}</p>
            <p><strong>Size:</strong> {len(data):,} characters</p>
            <p><strong>Lines:</strong> {data.count(chr(10))+1 if data else 0}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.text_area("Preview", data[:2000], height=150)

elif page == "Terminal":
    st.markdown("<h2>🖥️ System Terminal</h2>", unsafe_allow_html=True)
    st.warning("⚠️ Executes real backend commands. Destructive operations are blocked.")
    
    cmd = st.text_area("Command", height=100, placeholder="df -h && free -h && uptime")
    
    if st.button("▶️ Execute", use_container_width=True):
        with st.spinner("⏳ Running..."):
            st.session_state.terminal = post("/system/exec", {"command": cmd, "timeout": 120}, 140)
    
    if "terminal" in st.session_state:
        o = st.session_state.terminal
        st.markdown(f"""
        <div class='term'>$ {o.get('command','')}\n
STDOUT:\n{o.get('stdout','')}\n
STDERR:\n{o.get('stderr','')}\n
Exit Code: {o.get('returncode')}</div>
        """, unsafe_allow_html=True)

elif page == "Artifacts":
    st.markdown("<h2>📦 Artifact Factory</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Title", "Untitled")
    with col2:
        fmt = st.selectbox("Format", ["markdown", "html", "xlsx", "csv"])
    
    content = st.text_area("Content", height=200)
    
    if st.button("✨ Create Artifact", use_container_width=True):
        result = post("/artifact/create", {"title": title, "format": fmt, "content": content})
        if "error" not in result:
            st.success("✅ Artifact created!")
            st.json(result)
        else:
            st.error(f"❌ Error: {result['error']}")

elif page == "Library":
    st.markdown("<h2>📚 Library</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        title = st.text_input("Title", key="lib_title")
    with col2:
        typ = st.selectbox("Type", ["Document","Website","Spreadsheet","Note","Code","Other"])
    with col3:
        if st.button("💾 Save", use_container_width=True):
            content = st.session_state.get("lib_content", "")
            post("/library/add", {"title": title or "Untitled", "type": typ, "content": content})
            st.success("✅ Saved to library!")
    
    content = st.text_area("Content", height=150, key="lib_content")
    
    st.divider()
    state = get("/state")
    if state.get("library"):
        st.markdown("<h3>📖 Saved Items</h3>", unsafe_allow_html=True)
        cols = st.columns(2)
        for i, item in enumerate(state.get("library", [])):
            with cols[i % 2]:
                st.markdown(f"""
                <div class='item'>
                    <h4>📄 {item.get('title', 'Untitled')}</h4>
                    <p><strong>{item.get('type', 'N/A')}</strong></p>
                    <p class='muted'>{item.get('content', '')[:150]}...</p>
                </div>
                """, unsafe_allow_html=True)

elif page == "Settings":
    st.markdown("<h2>⚙️ Settings</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3>🎨 UI Settings</h3>", unsafe_allow_html=True)
        if st.button("Toggle Dark Mode"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    with col2:
        st.markdown("<h3>ℹ️ System Info</h3>", unsafe_allow_html=True)
        info = get("/health")
        st.markdown(f"""
        - **Service:** {info.get('service')}
        - **Version:** {info.get('version')}
        - **Status:** {info.get('status')}
        - **Timestamp:** {info.get('timestamp')}
        """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #64748b; font-size: 0.9rem; margin-top: 2rem;'>
    <p>⚡ Supreme AI Agent OS | Production Ready | Enterprise Grade</p>
    <p style='font-size: 0.8rem;'>© 2024 Cryptostoner94 | Powered by FastAPI + Streamlit</p>
</div>
""", unsafe_allow_html=True)
