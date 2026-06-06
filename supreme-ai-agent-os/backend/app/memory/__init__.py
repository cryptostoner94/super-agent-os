"""
Unified memory layer — SQLite (always on) + Redis (optional short-term).

SQLite stores: conversations, outcomes, events, agent state, artifacts.
Redis stores:  short-term context windows, task queues, live state.

No Postgres required. Zero external infra for baseline operation.
Redis is optional — gracefully degraded if unavailable.
"""
from __future__ import annotations
import asyncio, json, os, time
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import Column, Integer, String, Float, JSON, Text, select, text

# ── Paths ────────────────────────────────────────────────────────────────────
_DB_DIR = Path(os.getenv("SUPREME_DB_DIR", str(Path.home() / ".supreme-os" / "state")))
_DB_DIR.mkdir(parents=True, exist_ok=True)
_DB_URL = f"sqlite+aiosqlite:///{_DB_DIR}/memory.db"

engine = create_async_engine(_DB_URL, echo=False, connect_args={"check_same_thread": False})
Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ── Schema ────────────────────────────────────────────────────────────────────
class Base(DeclarativeBase): pass

class Outcome(Base):
    __tablename__ = "outcomes"
    id      = Column(Integer, primary_key=True)
    agent   = Column(String, index=True)
    goal    = Column(Text)
    step    = Column(JSON)
    result  = Column(JSON)
    score   = Column(Float)
    created = Column(Float, default=time.time)

class Event(Base):
    __tablename__ = "events"
    id      = Column(Integer, primary_key=True)
    kind    = Column(String, index=True)
    payload = Column(JSON)
    created = Column(Float, default=time.time)

class Conversation(Base):
    __tablename__ = "conversations"
    id         = Column(Integer, primary_key=True)
    session_id = Column(String, index=True)
    role       = Column(String)
    content    = Column(Text)
    agent      = Column(String)
    created    = Column(Float, default=time.time)

class AgentState(Base):
    __tablename__ = "agent_state"
    id      = Column(Integer, primary_key=True)
    agent   = Column(String, unique=True, index=True)
    state   = Column(JSON)
    updated = Column(Float, default=time.time)

# ── Init ──────────────────────────────────────────────────────────────────────
async def init_db():
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)

# ── Redis (optional) ──────────────────────────────────────────────────────────
_redis = None

async def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
        await r.ping()
        _redis = r
        return _redis
    except Exception:
        return None

# ── Write ops ─────────────────────────────────────────────────────────────────
async def log_outcome(agent: str, goal: str, step: dict, result: Any, score: float):
    async with Session() as s:
        s.add(Outcome(agent=agent, goal=goal, step=step, result=result, score=score))
        await s.commit()

async def log_event(kind: str, payload: Any):
    async with Session() as s:
        s.add(Event(kind=kind, payload=payload if isinstance(payload, dict) else {"data": str(payload)}))
        await s.commit()

async def save_message(session_id: str, role: str, content: str, agent: str = "system"):
    async with Session() as s:
        s.add(Conversation(session_id=session_id, role=role, content=content, agent=agent))
        await s.commit()
    # Mirror to Redis short-term buffer
    r = await _get_redis()
    if r:
        key = f"ctx:{session_id}"
        await r.rpush(key, json.dumps({"role": role, "content": content[:2000]}))
        await r.ltrim(key, -20, -1)   # keep last 20 messages
        await r.expire(key, 3600)

async def set_agent_state(agent: str, state: dict):
    async with Session() as s:
        existing = await s.execute(select(AgentState).where(AgentState.agent == agent))
        row = existing.scalar_one_or_none()
        if row:
            row.state = state
            row.updated = time.time()
        else:
            s.add(AgentState(agent=agent, state=state))
        await s.commit()

# ── Read ops ──────────────────────────────────────────────────────────────────
async def recall_similar(agent: str, goal: str, k: int = 5) -> list[dict]:
    async with Session() as s:
        rows = await s.execute(
            select(Outcome).where(Outcome.agent == agent, Outcome.score > 0.5)
            .order_by(Outcome.created.desc()).limit(k)
        )
        return [{"goal": r.goal, "step": r.step, "result": r.result, "score": r.score}
                for r in rows.scalars()]

async def get_conversation(session_id: str, limit: int = 20) -> list[dict]:
    r = await _get_redis()
    if r:
        raw = await r.lrange(f"ctx:{session_id}", -limit, -1)
        if raw:
            return [json.loads(m) for m in raw]
    async with Session() as s:
        rows = await s.execute(
            select(Conversation).where(Conversation.session_id == session_id)
            .order_by(Conversation.created.desc()).limit(limit)
        )
        msgs = [{"role": r.role, "content": r.content} for r in rows.scalars()]
        return list(reversed(msgs))

async def get_events(limit: int = 50) -> list[dict]:
    async with Session() as s:
        rows = await s.execute(
            select(Event).order_by(Event.created.desc()).limit(limit)
        )
        return [{"kind": r.kind, "payload": r.payload, "created": r.created}
                for r in rows.scalars()]

async def get_outcomes(agent: str | None = None, limit: int = 50) -> list[dict]:
    async with Session() as s:
        q = select(Outcome).order_by(Outcome.created.desc()).limit(limit)
        if agent:
            q = q.where(Outcome.agent == agent)
        rows = await s.execute(q)
        return [{"agent": r.agent, "goal": r.goal, "score": r.score, "created": r.created}
                for r in rows.scalars()]

async def memory_stats() -> dict:
    async with Session() as s:
        events   = (await s.execute(text("SELECT COUNT(*) FROM events"))).scalar()
        outcomes = (await s.execute(text("SELECT COUNT(*) FROM outcomes"))).scalar()
        convos   = (await s.execute(text("SELECT COUNT(*) FROM conversations"))).scalar()
    r = await _get_redis()
    redis_ok = r is not None
    return {"events": events, "outcomes": outcomes, "conversations": convos,
            "sqlite": True, "redis": redis_ok, "db_path": str(_DB_DIR / "memory.db")}

if __name__ == "__main__":
    asyncio.run(init_db())
    print("DB initialized at", _DB_DIR / "memory.db")
