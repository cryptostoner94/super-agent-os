"""
Gmail SMTP notification engine for the bounty pipeline.
Sends bulk summary emails to the agent operator when pending reports need attention.
Only sends every 48 hours (or when first pending report arrives).
"""
from __future__ import annotations

import os
import smtplib
import sqlite3
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ── Config (all from env) ─────────────────────────────────────────────────────
AGENT_EMAIL = os.getenv("AGENT_EMAIL", "")
AGENT_EMAIL_PASSWORD = os.getenv("AGENT_EMAIL_PASSWORD", "")
NOTIFY_TO = os.getenv("AGENT_EMAIL", "")  # send to self by default

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
NOTIFY_INTERVAL_S = 48 * 60 * 60  # 48 hours

DB_PATH = Path("data/pipeline.db")


# ── DB helpers ────────────────────────────────────────────────────────────────

def _db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    # Ensure table exists even if pipeline.py hasn't run yet
    con.execute("""
        CREATE TABLE IF NOT EXISTS pending_reports (
            id          TEXT PRIMARY KEY,
            platform    TEXT NOT NULL,
            program     TEXT NOT NULL,
            title       TEXT NOT NULL,
            severity    TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'pending',
            created_at  REAL NOT NULL,
            notified_at REAL
        )
    """)
    con.commit()
    return con


# ── Email sending ─────────────────────────────────────────────────────────────

def send_email(
    subject: str,
    body: str,
    to_email: str | None = None,
) -> dict:
    """
    Send an email via Gmail SMTP with STARTTLS.
    Credentials come from AGENT_EMAIL and AGENT_EMAIL_PASSWORD env vars.
    Returns {"ok": True/False, "error": str|None}
    """
    if not AGENT_EMAIL or not AGENT_EMAIL_PASSWORD:
        return {"ok": False, "error": "AGENT_EMAIL or AGENT_EMAIL_PASSWORD not set"}

    recipient = to_email or NOTIFY_TO
    if not recipient:
        return {"ok": False, "error": "No recipient email address available"}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = AGENT_EMAIL
        msg["To"] = recipient

        # Plain text version
        plain = body
        # HTML version (convert basic markdown to HTML)
        html_body = _markdown_to_html(body)

        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(AGENT_EMAIL, AGENT_EMAIL_PASSWORD)  # NOSONAR - credentials from env vars
            smtp.sendmail(AGENT_EMAIL, [recipient], msg.as_string())

        return {"ok": True, "to": recipient, "subject": subject}
    except smtplib.SMTPAuthenticationError as e:
        return {"ok": False, "error": f"SMTP authentication failed: {e}"}
    except smtplib.SMTPException as e:
        return {"ok": False, "error": f"SMTP error: {e}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _markdown_to_html(text: str) -> str:
    """Minimal markdown → HTML converter for email bodies."""
    import html as html_mod
    lines = text.split("\n")
    html_lines: list[str] = ["<html><body style='font-family:monospace;'>"]
    in_table = False

    for line in lines:
        # Table row
        if line.startswith("|"):
            if not in_table:
                html_lines.append("<table border='1' cellpadding='4' cellspacing='0'>")
                in_table = True
            cells = [c.strip() for c in line.split("|")[1:-1]]
            tag = "th" if set("".join(cells)) <= set("-| ") else "td"
            if tag == "th" and all(set(c) <= set("- ") for c in cells):
                continue  # skip separator row
            html_lines.append(
                "<tr>" + "".join(f"<{tag}>{html_mod.escape(c)}</{tag}>" for c in cells) + "</tr>"
            )
            continue
        else:
            if in_table:
                html_lines.append("</table>")
                in_table = False

        escaped = html_mod.escape(line)
        if line.startswith("## "):
            html_lines.append(f"<h2>{html_mod.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            html_lines.append(f"<h1>{html_mod.escape(line[2:])}</h1>")
        elif line.startswith("- "):
            html_lines.append(f"<li>{escaped[2:]}</li>")
        elif line.startswith("**") and line.endswith("**"):
            html_lines.append(f"<strong>{html_mod.escape(line[2:-2])}</strong><br>")
        elif line.strip() == "":
            html_lines.append("<br>")
        else:
            html_lines.append(f"{escaped}<br>")

    if in_table:
        html_lines.append("</table>")
    html_lines.append("</body></html>")
    return "\n".join(html_lines)


# ── Pending report queries ─────────────────────────────────────────────────────

def get_pending_reports() -> list[dict]:
    """
    Return pending reports that have not been notified yet,
    or whose last notification was more than 48 hours ago.
    """
    now = time.time()
    cutoff = now - NOTIFY_INTERVAL_S
    try:
        con = _db()
        rows = con.execute(
            """
            SELECT * FROM pending_reports
            WHERE status IN ('pending', 'approved')
              AND (notified_at IS NULL OR notified_at < ?)
            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 0
                    WHEN 'high'     THEN 1
                    WHEN 'medium'   THEN 2
                    ELSE                 3
                END,
                created_at DESC
            """,
            (cutoff,),
        ).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_all_pending_reports() -> list[dict]:
    """Return all pending reports regardless of notification time (for queue endpoint)."""
    try:
        con = _db()
        rows = con.execute(
            """
            SELECT * FROM pending_reports
            WHERE status IN ('pending', 'approved')
            ORDER BY created_at DESC
            """
        ).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


# ── Notification body builder ─────────────────────────────────────────────────

def build_notification_body(reports: list[dict]) -> str:
    """
    Build a markdown-formatted email body with a table of pending reports.
    """
    from datetime import datetime, timezone

    count = len(reports)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = [
        "# Supreme AI Agent OS — Bounty Pipeline Alert",
        f"",
        f"**Generated:** {now_str}",
        f"**Pending reports requiring attention:** {count}",
        f"",
        "---",
        f"",
        "## Pending Reports",
        f"",
        "| # | Platform | Program | Severity | Title | Status | Created | Action Needed |",
        "|---|----------|---------|----------|-------|--------|---------|---------------|",
    ]

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_reports = sorted(
        reports,
        key=lambda r: (severity_order.get(r.get("severity", "low"), 3), -r.get("created_at", 0)),
    )

    for i, rep in enumerate(sorted_reports, start=1):
        created_ts = rep.get("created_at", 0)
        try:
            created_str = datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        except Exception:
            created_str = "unknown"

        severity = rep.get("severity", "low").upper()
        status = rep.get("status", "pending")
        action = "Review & approve for submission" if status == "pending" else "Awaiting submission"

        lines.append(
            f"| {i} | {rep.get('platform', '')} | {rep.get('program', '')} "
            f"| {severity} | {rep.get('title', '')[:60]} | {status} | {created_str} | {action} |"
        )

    lines += [
        f"",
        "---",
        f"",
        "## Actions",
        f"",
        "- **Approve a report:** `POST /pipeline/queue/{{id}}/approve`",
        "- **Discard a report:** `DELETE /pipeline/queue/{{id}}`",
        "- **View all queued:** `GET /pipeline/queue`",
        "- **Preview notification:** `GET /pipeline/notify/preview`",
        f"",
        "---",
        f"*This is an automated message from Supreme AI Agent OS.*",
        f"*Next notification will be sent in 48 hours if items remain pending.*",
    ]

    return "\n".join(lines)


# ── Main notification logic ────────────────────────────────────────────────────

def notify_if_needed() -> dict:
    """
    Check for pending reports. If any exist and we haven't notified in the last
    48 hours, send a summary email. Returns {"sent": bool, "reason": str}.
    """
    reports = get_pending_reports()
    if not reports:
        return {"sent": False, "reason": "no_pending_reports"}

    body = build_notification_body(reports)
    count = len(reports)
    severities = [r.get("severity", "low") for r in reports]
    has_critical = "critical" in severities
    has_high = "high" in severities

    if has_critical:
        subject = f"[CRITICAL] Supreme AI Agent OS — {count} bounty report(s) need review"
    elif has_high:
        subject = f"[HIGH] Supreme AI Agent OS — {count} bounty report(s) need review"
    else:
        subject = f"Supreme AI Agent OS — {count} bounty report(s) need review"

    result = send_email(subject, body)

    if result.get("ok"):
        report_ids = [r["id"] for r in reports]
        mark_notified(report_ids)
        return {"sent": True, "count": count, "reason": "notification_sent", "to": result.get("to")}

    return {"sent": False, "reason": f"email_failed: {result.get('error')}"}


def mark_notified(report_ids: list[str]) -> None:
    """Update notified_at timestamp for a list of report IDs."""
    if not report_ids:
        return
    now = time.time()
    try:
        con = _db()
        placeholders = ",".join("?" * len(report_ids))
        con.execute(
            f"UPDATE pending_reports SET notified_at = ? WHERE id IN ({placeholders})",
            [now, *report_ids],
        )
        con.commit()
        con.close()
    except Exception:
        pass
