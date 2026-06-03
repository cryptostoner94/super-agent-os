from __future__ import annotations
import time
import uuid
from fastapi import FastAPI
from backend.app.core.config import settings, capabilities
from backend.app.api.schemas import AgentRequest, CommandRequest, LibraryItem, ArtifactRequest
from backend.app.agents.brain import run_agent
from backend.app.agents.registry import AGENTS
from backend.app.skills.registry import SKILLS
from backend.app.runtime.executor import execute
from backend.app.artifacts.factory import create_markdown, create_html, create_xlsx, create_csv
from backend.app.memory.store import load_state, add_library
from backend.app.connectors.status import connector_status

app = FastAPI(title=settings.app_name, version="0.1.0")

@app.get("/")
@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name, "time": time.time()}

@app.get("/capabilities")
def get_capabilities():
    return capabilities()

@app.get("/agents")
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

@app.post("/agent/run")
def agent_run(req: AgentRequest):
    result = run_agent(req.prompt, req.raw_data, req.file_text, req.agent_id)
    return result

@app.post("/system/exec")
def system_exec(req: CommandRequest):
    return execute(req.command, req.timeout)

@app.post("/library/add")
def library_add(req: LibraryItem):
    item = {"id": str(uuid.uuid4()), "title": req.title, "type": req.type, "content": req.content, "created": time.time()}
    return {"ok": True, "item": add_library(item)}

@app.post("/artifact/create")
def artifact_create(req: ArtifactRequest):
    fmt = req.format.lower().strip()
    if fmt == "html":
        return create_html(req.title, req.content)
    if fmt == "xlsx":
        return create_xlsx(req.content)
    if fmt == "csv":
        return create_csv(req.content)
    return create_markdown(req.title, req.content)
