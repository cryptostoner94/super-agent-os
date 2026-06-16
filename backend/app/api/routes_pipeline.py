"""
FastAPI router for the bounty pipeline.
Prefix: /pipeline
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.app.core.bounty_pipeline import (
    DB_PATH,
    get_last_run,
    get_queued_reports,
    run_pipeline,
    submit_report_api,
)
from backend.app.core.notification_engine import (
    build_notification_body,
    get_all_pending_reports,
    get_pending_reports,
)
from backend.app.core.pipeline_scheduler import get_scheduler_state

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# ── In-memory job tracker (lightweight; not persisted across restarts) ─────────
_jobs: dict[str, dict] = {}


async def _run_pipeline_job(job_id: str, platforms: list[str], top_n: int) -> None:
    """Background coroutine that runs the pipeline and records the result."""
    _jobs[job_id]["status"] = "running"
    _jobs[job_id]["started_at"] = time.time()
    try:
        result = await run_pipeline(platforms=platforms, top_n=top_n)
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["result"] = result
    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
    finally:
        _jobs[job_id]["finished_at"] = time.time()


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/status")
async def pipeline_status() -> dict:
    """
    Return last pipeline run time and counts (identified, executed, submitted, queued).
    Also includes scheduler state.
    """
    last_run = get_last_run()
    scheduler = get_scheduler_state()

    # Aggregate queue counts from DB
    queued_reports = get_queued_reports()
    queue_counts: dict[str, int] = {}
    for r in queued_reports:
        status = r.get("status", "pending")
        queue_counts[status] = queue_counts.get(status, 0) + 1

    return {
        "ok": True,
        "scheduler": {
            "running": scheduler.get("running", False),
            "pipeline_last_run": scheduler.get("pipeline_last_run"),
            "notify_last_run": scheduler.get("notify_last_run"),
            "pipeline_runs": scheduler.get("pipeline_runs", 0),
            "notify_runs": scheduler.get("notify_runs", 0),
        },
        "last_pipeline_run": {
            "id": last_run.get("id"),
            "started_at": last_run.get("started_at"),
            "finished_at": last_run.get("finished_at"),
            "identified": last_run.get("identified", 0),
            "executed": last_run.get("executed", 0),
            "submitted": last_run.get("submitted", 0),
            "queued": last_run.get("queued", 0),
            "errors": last_run.get("errors", []),
        },
        "queue_totals": queue_counts,
        "queue_pending": queue_counts.get("pending", 0),
        "active_jobs": {
            job_id: {k: v for k, v in job.items() if k != "result"}
            for job_id, job in _jobs.items()
        },
    }


# ── Manual trigger ────────────────────────────────────────────────────────────

@router.post("/run")
async def trigger_pipeline(
    background_tasks: BackgroundTasks,
    payload: dict = {},
) -> dict:
    """
    Trigger a pipeline run manually.
    Returns a job_id immediately; the pipeline runs in the background.
    Body (optional): {"platforms": ["hackerone", ...], "top_n": 5}
    """
    platforms: list[str] = payload.get("platforms") or ["hackerone", "intigriti", "yeswehack"]
    top_n = int(payload.get("top_n") or 5)
    if top_n < 1 or top_n > 50:
        raise HTTPException(400, "top_n must be between 1 and 50")

    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "platforms": platforms,
        "top_n": top_n,
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
        "result": None,
        "error": None,
    }

    background_tasks.add_task(_run_pipeline_job, job_id, platforms, top_n)

    return {
        "ok": True,
        "job_id": job_id,
        "message": f"Pipeline started. job_id={job_id}. Check GET /pipeline/jobs/{job_id} for progress.",
        "platforms": platforms,
        "top_n": top_n,
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    """Return the status and result of a specific pipeline job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    return job


# ── Queue management ──────────────────────────────────────────────────────────

@router.get("/queue")
async def list_queue(
    status: str | None = None,
    platform: str | None = None,
    severity: str | None = None,
    limit: int = 50,
) -> dict:
    """
    List pending reports from the approval queue.
    Optional query filters: status, platform, severity.
    """
    reports = get_queued_reports()

    if status:
        reports = [r for r in reports if r.get("status") == status]
    if platform:
        reports = [r for r in reports if r.get("platform") == platform]
    if severity:
        reports = [r for r in reports if r.get("severity") == severity]

    reports = reports[:limit]

    # Enrich with parsed findings for richer output
    for rep in reports:
        try:
            rep["findings"] = json.loads(rep.get("findings_json", "{}"))
        except Exception:
            rep["findings"] = {}

    return {
        "ok": True,
        "count": len(reports),
        "reports": reports,
    }


@router.post("/queue/{report_id}/approve")
async def approve_report(report_id: str) -> dict:
    """
    Approve a queued report: change status to 'approved' and attempt API submission.
    If submission succeeds, status → 'submitted'. Otherwise, status → 'approved'.
    """
    try:
        con = sqlite3.connect(str(DB_PATH))
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT * FROM pending_reports WHERE id = ?", (report_id,)
        ).fetchone()
        if not row:
            con.close()
            raise HTTPException(404, f"Report {report_id} not found")
        rep = dict(row)

        # Mark approved before attempting submission
        con.execute(
            "UPDATE pending_reports SET status = 'approved' WHERE id = ?", (report_id,)
        )
        con.commit()
        con.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")

    # Reconstruct report data from stored findings_json
    try:
        report_data: dict = json.loads(rep.get("findings_json", "{}"))
    except Exception:
        report_data = {}

    if not report_data:
        report_data = {
            "id": rep["id"],
            "platform": rep["platform"],
            "program": rep["program"],
            "title": rep["title"],
            "severity": rep["severity"],
        }

    submit_result = await submit_report_api(report_data, rep["platform"])

    if submit_result.get("ok"):
        try:
            con = sqlite3.connect(str(DB_PATH))
            con.execute(
                "UPDATE pending_reports SET status = 'submitted' WHERE id = ?", (report_id,)
            )
            con.commit()
            con.close()
        except Exception:
            pass
        return {
            "ok": True,
            "report_id": report_id,
            "action": "submitted",
            "platform_report_id": submit_result.get("report_id"),
            "message": "Report approved and successfully submitted to platform.",
        }

    return {
        "ok": False,
        "report_id": report_id,
        "action": "approved_pending_manual",
        "submit_error": submit_result.get("error"),
        "message": (
            "Report marked as approved but API submission failed. "
            "Please submit manually via the platform web interface."
        ),
    }


@router.delete("/queue/{report_id}")
async def discard_report(report_id: str) -> dict:
    """Discard (soft-delete) a queued report by marking its status as 'discarded'."""
    try:
        con = sqlite3.connect(str(DB_PATH))
        cur = con.execute(
            "UPDATE pending_reports SET status = 'discarded' "
            "WHERE id = ? AND status NOT IN ('submitted', 'discarded')",
            (report_id,),
        )
        affected = cur.rowcount
        con.commit()
        con.close()
    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")

    if affected == 0:
        # Determine if not found vs already in terminal state
        try:
            con = sqlite3.connect(str(DB_PATH))
            row = con.execute(
                "SELECT status FROM pending_reports WHERE id = ?", (report_id,)
            ).fetchone()
            con.close()
        except Exception:
            row = None

        if row is None:
            raise HTTPException(404, f"Report {report_id} not found")
        return {
            "ok": False,
            "report_id": report_id,
            "message": f"Report is in status '{row[0]}' and cannot be discarded.",
        }

    return {
        "ok": True,
        "report_id": report_id,
        "action": "discarded",
        "message": "Report discarded and will not be submitted.",
    }


# ── Notification preview ──────────────────────────────────────────────────────

@router.get("/notify/preview")
async def notify_preview() -> dict:
    """
    Preview the next notification email without actually sending it.
    Shows both all-pending and the subset that is due for notification (> 48h window).
    """
    all_reports = get_all_pending_reports()
    due_reports = get_pending_reports()  # subset actually past the 48h window

    if not all_reports:
        return {
            "ok": True,
            "pending_count": 0,
            "due_for_notification": 0,
            "would_send": False,
            "reason": "no_pending_reports",
            "preview": None,
        }

    preview_reports = due_reports if due_reports else all_reports
    body = build_notification_body(preview_reports)

    return {
        "ok": True,
        "pending_count": len(all_reports),
        "due_for_notification": len(due_reports),
        "would_send": len(due_reports) > 0,
        "reason": "pending_reports_due" if due_reports else "notification_not_yet_due",
        "preview": {
            "subject": _build_subject(preview_reports),
            "body": body,
            "recipient": os.getenv("AGENT_EMAIL", "(not configured)"),
        },
    }


def _build_subject(reports: list[dict]) -> str:
    count = len(reports)
    severities = {r.get("severity") for r in reports}
    if "critical" in severities:
        return f"[CRITICAL] Supreme AI Agent OS — {count} bounty report(s) need review"
    if "high" in severities:
        return f"[HIGH] Supreme AI Agent OS — {count} bounty report(s) need review"
    return f"Supreme AI Agent OS — {count} bounty report(s) need review"


# ── Send notification now (manual trigger) ────────────────────────────────────

@router.post("/notify/send")
async def send_notification_now() -> dict:
    """
    Manually trigger a notification email immediately, bypassing the 48h window.
    Useful for testing or urgent operator alerts.
    """
    from backend.app.core.notification_engine import (
        mark_notified,
        send_email,
    )

    reports = get_all_pending_reports()
    if not reports:
        return {"ok": True, "sent": False, "reason": "no_pending_reports"}

    body = build_notification_body(reports)
    subject = _build_subject(reports)
    result = send_email(subject, body)

    if result.get("ok"):
        mark_notified([r["id"] for r in reports])
        return {
            "ok": True,
            "sent": True,
            "count": len(reports),
            "to": result.get("to"),
        }

    return {
        "ok": False,
        "sent": False,
        "error": result.get("error"),
    }
