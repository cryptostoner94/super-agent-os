"""
Background scheduler for the bounty pipeline.
Runs the full pipeline every 6 hours and checks for notification needs every 2 hours.
Designed to be started as an asyncio background task on FastAPI startup.
"""
from __future__ import annotations

import asyncio
import logging
import time

logger = logging.getLogger("pipeline_scheduler")

# Intervals
PIPELINE_INTERVAL_S = 6 * 60 * 60   # 6 hours
NOTIFY_INTERVAL_S   = 2 * 60 * 60   # 2 hours

# State tracking
_scheduler_state: dict = {
    "running": False,
    "pipeline_last_run": None,
    "notify_last_run": None,
    "pipeline_runs": 0,
    "notify_runs": 0,
    "errors": [],
}


def get_scheduler_state() -> dict:
    """Return a snapshot of the scheduler's current state."""
    return _scheduler_state.copy()


async def _run_pipeline_job() -> None:
    """Execute the full bounty pipeline."""
    from backend.app.core.bounty_pipeline import run_pipeline

    _scheduler_state["pipeline_last_run"] = time.time()
    try:
        result = await run_pipeline(platforms=["hackerone", "intigriti", "yeswehack"], top_n=5)
        _scheduler_state["pipeline_runs"] += 1
        logger.info(
            "[pipeline_scheduler] pipeline run complete — "
            "identified=%d executed=%d submitted=%d queued=%d",
            result.get("identified", 0),
            result.get("executed", 0),
            result.get("submitted", 0),
            result.get("queued", 0),
        )
    except Exception as e:
        err = f"pipeline run error: {e}"
        logger.error("[pipeline_scheduler] %s", err)
        _scheduler_state["errors"].append({"at": time.time(), "error": err})
        # Keep errors list bounded
        if len(_scheduler_state["errors"]) > 50:
            _scheduler_state["errors"] = _scheduler_state["errors"][-50:]


async def _run_notify_job() -> None:
    """Check if a notification email needs to be sent."""
    from backend.app.core.notification_engine import notify_if_needed

    _scheduler_state["notify_last_run"] = time.time()
    try:
        result = notify_if_needed()
        _scheduler_state["notify_runs"] += 1
        if result.get("sent"):
            logger.info(
                "[pipeline_scheduler] notification sent — count=%d to=%s",
                result.get("count", 0),
                result.get("to", ""),
            )
        else:
            logger.debug(
                "[pipeline_scheduler] notification skipped — reason=%s",
                result.get("reason", ""),
            )
    except Exception as e:
        err = f"notify job error: {e}"
        logger.error("[pipeline_scheduler] %s", err)
        _scheduler_state["errors"].append({"at": time.time(), "error": err})
        if len(_scheduler_state["errors"]) > 50:
            _scheduler_state["errors"] = _scheduler_state["errors"][-50:]


async def _pipeline_loop() -> None:
    """Run pipeline every PIPELINE_INTERVAL_S seconds."""
    # Small initial delay to let the app fully start up
    await asyncio.sleep(30)
    while True:
        await _run_pipeline_job()
        await asyncio.sleep(PIPELINE_INTERVAL_S)


async def _notify_loop() -> None:
    """Check for notification needs every NOTIFY_INTERVAL_S seconds."""
    # Offset from pipeline start to avoid simultaneous startup load
    await asyncio.sleep(60)
    while True:
        await _run_notify_job()
        await asyncio.sleep(NOTIFY_INTERVAL_S)


async def start_scheduler() -> None:
    """
    Entry point called from FastAPI lifespan / startup.
    Starts both background loops as fire-and-forget asyncio tasks.
    This coroutine returns immediately; the loops run in the background.
    """
    if _scheduler_state["running"]:
        logger.warning("[pipeline_scheduler] already running, skipping duplicate start")
        return

    _scheduler_state["running"] = True
    logger.info(
        "[pipeline_scheduler] starting — pipeline every %dh, notify every %dh",
        PIPELINE_INTERVAL_S // 3600,
        NOTIFY_INTERVAL_S // 3600,
    )

    asyncio.create_task(_pipeline_loop(), name="bounty_pipeline_loop")
    asyncio.create_task(_notify_loop(), name="bounty_notify_loop")
