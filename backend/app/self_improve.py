"""Nightly self-improvement loop — outcome-driven agent tuning."""
from __future__ import annotations
import time
import structlog
from sqlalchemy import text
from backend.app.memory import Session

log = structlog.get_logger()


async def nightly_retune():
    """Pull last 24h outcomes, compute per-agent success rates, surface failing patterns."""
    cutoff = time.time() - 86400
    async with Session() as s:
        rows = await s.execute(text("""
            SELECT agent, COUNT(*) n, AVG(score) avg_score
            FROM outcomes
            WHERE created > :cutoff
            GROUP BY agent
        """), {"cutoff": cutoff})
        stats = [dict(r._mapping) for r in rows]
    log.info("retune.stats", stats=stats)
    return stats
