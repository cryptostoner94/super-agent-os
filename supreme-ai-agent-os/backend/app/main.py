"""
Supreme AI Agent OS - FastAPI Backend
Production-ready REST API with logging, error handling, and middleware
"""
from __future__ import annotations
import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from backend.app.core.config import settings, capabilities
from backend.app.api.schemas import AgentRequest, CommandRequest, LibraryItem, ArtifactRequest
from backend.app.agents.brain import run_agent
from backend.app.agents.registry import AGENTS
from backend.app.skills.registry import SKILLS
from backend.app.runtime.executor import execute
from backend.app.artifacts.factory import create_markdown, create_html, create_xlsx, create_csv
from backend.app.memory.store import load_state, add_library
from backend.app.connectors.status import connector_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Startup/Shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 {settings.app_name} starting up...")
    yield
    logger.info(f"🛑 {settings.app_name} shutting down...")

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Enterprise AI Agent Operating System",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)"
    )
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc)},
    )

# Health Endpoints
@app.get("/", tags=["health"])
@app.get("/health", tags=["health"])
def health():
    """System health check endpoint"""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "1.0.0",
        "time": time.time(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/ready", tags=["health"])
def ready():
    """Readiness probe - checks if system is ready to handle requests"""
    return {"ready": True, "service": settings.app_name}

@app.get("/live", tags=["health"])
def live():
    """Liveness probe - checks if system is alive"""
    return {"alive": True}

# Capability Endpoints
@app.get("/capabilities", tags=["system"])
def get_capabilities():
    """Get available capabilities and integrations"""
    try:
        return capabilities()
    except Exception as e:
        logger.error(f"Error fetching capabilities: {str(e)}")
        return {"error": str(e)}

@app.get("/agents", tags=["agents"])
def get_agents():
    """List all available agents"""
    try:
        return AGENTS
    except Exception as e:
        logger.error(f"Error fetching agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/skills", tags=["skills"])
def get_skills():
    """List all available skills"""
    try:
        return SKILLS
    except Exception as e:
        logger.error(f"Error fetching skills: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/connectors", tags=["connectors"])
def get_connectors():
    """Get connector status"""
    try:
        return connector_status()
    except Exception as e:
        logger.error(f"Error fetching connectors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state", tags=["system"])
def state():
    """Get system state and library"""
    try:
        return load_state()
    except Exception as e:
        logger.error(f"Error loading state: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent Endpoints
@app.post("/agent/run", tags=["agents"])
def agent_run(req: AgentRequest):
    """Execute an agent with a prompt and optional data"""
    try:
        logger.info(f"Running agent: {req.agent_id}")
        result = run_agent(req.prompt, req.raw_data, req.file_text, req.agent_id)
        logger.info(f"Agent {req.agent_id} completed successfully")
        return result
    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# System Endpoints
@app.post("/system/exec", tags=["system"])
def system_exec(req: CommandRequest):
    """Execute system command (requires SUPREME_ALLOW_TERMINAL=true)"""
    try:
        if not settings.allow_terminal:
            raise HTTPException(status_code=403, detail="Terminal execution is disabled")
        
        logger.warning(f"Executing command: {req.command[:100]}...")
        return execute(req.command, req.timeout)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Command execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Library Endpoints
@app.post("/library/add", tags=["library"])
def library_add(req: LibraryItem):
    """Add item to library"""
    try:
        item = {
            "id": str(uuid.uuid4()),
            "title": req.title,
            "type": req.type,
            "content": req.content,
            "created": time.time()
        }
        logger.info(f"Adding to library: {item['id']}")
        return {"ok": True, "item": add_library(item)}
    except Exception as e:
        logger.error(f"Library add failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Artifact Endpoints
@app.post("/artifact/create", tags=["artifacts"])
def artifact_create(req: ArtifactRequest):
    """Create artifact in various formats"""
    try:
        fmt = req.format.lower().strip()
        logger.info(f"Creating artifact: {req.title} ({fmt})")
        
        if fmt == "html":
            return create_html(req.title, req.content)
        elif fmt == "xlsx":
            return create_xlsx(req.content)
        elif fmt == "csv":
            return create_csv(req.content)
        else:
            return create_markdown(req.title, req.content)
    except Exception as e:
        logger.error(f"Artifact creation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
