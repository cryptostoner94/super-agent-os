"""
Bounty hunting revenue pipeline — async orchestrator.
Identifies, recons, drafts, and submits vulnerability reports autonomously.
"""
from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# ── Credentials (all from env) ────────────────────────────────────────────────
H1_USER = os.getenv("HACKERONE_USERNAME", "")
H1_TOKEN = os.getenv("HACKERONE_API_TOKEN", "")
INTIGRITI_TOKEN = os.getenv("INTIGRITI_TOKEN", "")
YWH_TOKEN = os.getenv("YESWEHACK_TOKEN", "")

# ── Constants ─────────────────────────────────────────────────────────────────
RECON_TIMEOUT = 10
RECON_UA = "Mozilla/5.0 (Security Research Bot)"
DB_PATH = Path("data/pipeline.db")

COMMON_PATHS = ["/admin", "/api", "/.git", "/swagger", "/swagger-ui", "/openapi.json"]
SENSITIVE_HEADERS = ["Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options",
                     "Strict-Transport-Security", "Referrer-Policy"]

SEVERITY_MAP = {
    "cors_wildcard": "high",
    "missing_csp": "medium",
    "exposed_admin": "critical",
    "exposed_git": "high",
    "exposed_swagger": "medium",
    "exposed_api": "low",
    "missing_hsts": "medium",
    "missing_x_frame": "low",
    "missing_x_content_type": "low",
    "missing_referrer_policy": "low",
}


# ── DB initialisation ─────────────────────────────────────────────────────────

def _ensure_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
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
    con.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id          TEXT PRIMARY KEY,
            started_at  REAL NOT NULL,
            finished_at REAL,
            identified  INTEGER DEFAULT 0,
            executed    INTEGER DEFAULT 0,
            submitted   INTEGER DEFAULT 0,
            queued      INTEGER DEFAULT 0,
            summary_json TEXT
        )
    """)
    con.commit()
    con.close()


_ensure_db()


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_program(prog: dict) -> float:
    """
    score = bounty_max * response_efficiency / 100, weighted by resolved_reports.
    All values are treated as floats; missing values default to 0.
    """
    try:
        bounty_max = float(prog.get("max_bounty") or prog.get("bounty") or 0)
    except (TypeError, ValueError):
        bounty_max = 0.0

    try:
        response_eff = float(prog.get("response_efficiency") or 50)
    except (TypeError, ValueError):
        response_eff = 50.0

    try:
        resolved = float(prog.get("resolved_reports") or 0)
    except (TypeError, ValueError):
        resolved = 0.0

    base_score = bounty_max * response_eff / 100.0
    weight = 1.0 + (resolved / 1000.0)  # small bonus for active programs
    return round(base_score * weight, 2)


# ── Platform fetchers ─────────────────────────────────────────────────────────

async def _fetch_h1_programs() -> list[dict]:
    if not H1_TOKEN or not H1_USER:
        return []
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(
                "https://api.hackerone.com/v1/hackers/programs",
                auth=(H1_USER, H1_TOKEN),  # NOSONAR - credentials from env vars
                params={"page[size]": 50, "sort": "-started_accepting_at"},
                headers={"Accept": "application/json"},
            )
            r.raise_for_status()
            programs = []
            for p in r.json().get("data", []):
                attr = p.get("attributes", {})
                handle = attr.get("handle", "")
                # Extract in-scope URLs from the program
                targets: list[str] = []
                for scope_item in attr.get("structured_scope", {}).get("in_scope", []):
                    identifier = scope_item.get("identifier", "")
                    if identifier.startswith("http"):
                        targets.append(identifier)
                    elif "." in identifier and not identifier.startswith("*"):
                        targets.append(f"https://{identifier}")
                programs.append({
                    "platform": "hackerone",
                    "handle": handle,
                    "name": attr.get("name", handle),
                    "url": f"https://hackerone.com/{handle}",
                    "max_bounty": attr.get("max_bounty_table_value") or 0,
                    "response_efficiency": attr.get("response_efficiency_percentage") or 0,
                    "resolved_reports": attr.get("resolved_report_count") or 0,
                    "submission_state": attr.get("submission_state", ""),
                    "targets": targets,
                })
            return [p for p in programs if p.get("submission_state") == "open"]
    except Exception:
        return []


async def _fetch_intigriti_programs() -> list[dict]:
    if not INTIGRITI_TOKEN:
        return []
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                "https://api.intigriti.com/external/researcher/v1/programs",
                headers={"Authorization": f"Bearer {INTIGRITI_TOKEN}", "Accept": "application/json"},
            )
            r.raise_for_status()
            programs = []
            for p in r.json().get("records", []):
                max_b = p.get("maxBounty") or {}
                handle = p.get("handle") or str(p.get("id", ""))
                targets: list[str] = []
                for domain in p.get("domains", []):
                    identifier = domain.get("endpoint", "")
                    if identifier.startswith("http"):
                        targets.append(identifier)
                    elif "." in identifier and not identifier.startswith("*"):
                        targets.append(f"https://{identifier}")
                programs.append({
                    "platform": "intigriti",
                    "handle": handle,
                    "name": p.get("name", handle),
                    "url": f"https://app.intigriti.com/researcher/programs/{handle}",
                    "max_bounty": float(max_b.get("value") or 0),
                    "response_efficiency": 70,  # Intigriti doesn't expose this directly
                    "resolved_reports": 0,
                    "status": p.get("status", ""),
                    "targets": targets,
                })
            return [p for p in programs if p.get("status", "").lower() in ("open", "live")]
    except Exception:
        return []


async def _fetch_ywh_programs() -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            headers: dict[str, str] = {"Accept": "application/json"}
            if YWH_TOKEN:
                headers["Authorization"] = f"Bearer {YWH_TOKEN}"
            r = await c.get("https://api.yeswehack.com/programs", headers=headers)
            r.raise_for_status()
            items = r.json().get("items", [])
            programs = []
            for p in items[:100]:
                targets: list[str] = []
                for scope_item in p.get("scopes", []):
                    scope_val = scope_item.get("scope", "")
                    if scope_val.startswith("http"):
                        targets.append(scope_val)
                    elif "." in scope_val and not scope_val.startswith("*"):
                        targets.append(f"https://{scope_val}")
                programs.append({
                    "platform": "yeswehack",
                    "handle": p.get("slug", ""),
                    "name": p.get("title") or p.get("name", ""),
                    "url": f"https://yeswehack.com/programs/{p.get('slug', '')}",
                    "max_bounty": float(p.get("max_bounty") or 0),
                    "response_efficiency": 65,  # YWH doesn't expose this directly
                    "resolved_reports": 0,
                    "vdp": p.get("vdp", False),
                    "targets": targets,
                })
            return [p for p in programs if not p.get("vdp", True)]  # prefer bounty programs
    except Exception:
        return []


# ── Opportunity identification ────────────────────────────────────────────────

async def identify_opportunities(
    platforms: list[str] | None = None,
    top_n: int = 10,
) -> list[dict]:
    """Fetch all platforms in parallel, score, return top N by score."""
    if platforms is None:
        platforms = ["hackerone", "intigriti", "yeswehack"]

    tasks: list[asyncio.Task[list[dict]]] = []
    if "hackerone" in platforms:
        tasks.append(asyncio.create_task(_fetch_h1_programs()))
    if "intigriti" in platforms:
        tasks.append(asyncio.create_task(_fetch_intigriti_programs()))
    if "yeswehack" in platforms:
        tasks.append(asyncio.create_task(_fetch_ywh_programs()))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_programs: list[dict] = []
    for result in results:
        if isinstance(result, list):
            all_programs.extend(result)

    # Score and rank
    for prog in all_programs:
        prog["score"] = score_program(prog)

    ranked = sorted(all_programs, key=lambda p: p["score"], reverse=True)
    return ranked[:top_n]


# ── Reconnaissance ────────────────────────────────────────────────────────────

async def _probe_url(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    """Probe a single URL, return headers and status."""
    result: dict[str, Any] = {"url": url, "reachable": False, "status": None, "headers": {}}
    try:
        r = await client.head(url, follow_redirects=True)
        result["reachable"] = True
        result["status"] = r.status_code
        result["headers"] = dict(r.headers)
        result["final_url"] = str(r.url)
    except Exception:
        try:
            r = await client.get(url, follow_redirects=True)
            result["reachable"] = True
            result["status"] = r.status_code
            result["headers"] = dict(r.headers)
            result["final_url"] = str(r.url)
        except Exception as e:
            result["error"] = str(e)
    return result


async def execute_recon(program: dict) -> dict[str, Any]:
    """
    Run httpx HEAD/GET recon on program targets.
    Checks security headers and common misconfigs.
    Returns a structured findings dict.
    """
    targets = program.get("targets", [])
    if not targets:
        # Attempt to derive a target from the program URL as a fallback
        prog_url = program.get("url", "")
        if prog_url:
            # Use program name to guess a target domain
            handle = program.get("handle", "")
            if handle:
                targets = [f"https://{handle}.com"]

    findings: list[dict] = []
    probed: list[dict] = []

    async with httpx.AsyncClient(
        timeout=RECON_TIMEOUT,
        headers={"User-Agent": RECON_UA},
        follow_redirects=True,
    ) as client:
        # Probe base targets
        base_tasks = [_probe_url(client, t) for t in targets[:5]]  # limit to 5 targets
        base_results = await asyncio.gather(*base_tasks, return_exceptions=True)
        for br in base_results:
            if isinstance(br, dict):
                probed.append(br)

        # Probe common sensitive paths on the first reachable target
        base_url: str | None = None
        for bp in probed:
            if bp.get("reachable") and bp.get("status") and bp["status"] < 500:
                base_url = bp.get("final_url", bp["url"]).rstrip("/")
                break

        if base_url:
            path_tasks = [_probe_url(client, base_url + path) for path in COMMON_PATHS]
            path_results = await asyncio.gather(*path_tasks, return_exceptions=True)
            for i, pr in enumerate(path_results):
                if not isinstance(pr, dict):
                    continue
                path = COMMON_PATHS[i]
                status = pr.get("status")
                if status and status in (200, 201, 301, 302, 403):
                    # 403 on admin means it exists
                    finding_type = {
                        "/admin": "exposed_admin",
                        "/api": "exposed_api",
                        "/.git": "exposed_git",
                        "/swagger": "exposed_swagger",
                        "/swagger-ui": "exposed_swagger",
                        "/openapi.json": "exposed_swagger",
                    }.get(path, "exposed_path")
                    severity = SEVERITY_MAP.get(finding_type, "low")
                    if status in (200, 201) or (path == "/admin" and status == 403):
                        findings.append({
                            "type": finding_type,
                            "url": pr["url"],
                            "status": status,
                            "severity": severity,
                            "detail": f"Path {path} returned HTTP {status}",
                        })

            # Check security headers on the base target
            base_probe = next((p for p in probed if p.get("reachable")), None)
            if base_probe:
                headers_lower = {k.lower(): v for k, v in base_probe.get("headers", {}).items()}

                # CORS wildcard
                cors = headers_lower.get("access-control-allow-origin", "")
                if cors == "*":
                    findings.append({
                        "type": "cors_wildcard",
                        "url": base_probe["url"],
                        "severity": SEVERITY_MAP["cors_wildcard"],
                        "detail": "Access-Control-Allow-Origin: * allows any origin",
                    })

                # Missing CSP
                if "content-security-policy" not in headers_lower:
                    findings.append({
                        "type": "missing_csp",
                        "url": base_probe["url"],
                        "severity": SEVERITY_MAP["missing_csp"],
                        "detail": "Content-Security-Policy header is absent",
                    })

                # Missing HSTS
                if "strict-transport-security" not in headers_lower:
                    findings.append({
                        "type": "missing_hsts",
                        "url": base_probe["url"],
                        "severity": SEVERITY_MAP["missing_hsts"],
                        "detail": "Strict-Transport-Security header is absent",
                    })

                # Missing X-Frame-Options
                if "x-frame-options" not in headers_lower:
                    findings.append({
                        "type": "missing_x_frame",
                        "url": base_probe["url"],
                        "severity": SEVERITY_MAP["missing_x_frame"],
                        "detail": "X-Frame-Options header is absent (potential clickjacking)",
                    })

                # Missing X-Content-Type-Options
                if "x-content-type-options" not in headers_lower:
                    findings.append({
                        "type": "missing_x_content_type",
                        "url": base_probe["url"],
                        "severity": SEVERITY_MAP["missing_x_content_type"],
                        "detail": "X-Content-Type-Options header is absent (MIME sniffing risk)",
                    })

    return {
        "program": program.get("name"),
        "platform": program.get("platform"),
        "handle": program.get("handle"),
        "targets_probed": len(probed),
        "base_url": base_url,
        "findings": findings,
        "finding_count": len(findings),
        "recon_at": time.time(),
    }


# ── Report drafting ───────────────────────────────────────────────────────────

def _severity_for_findings(findings: list[dict]) -> str:
    """Return the highest severity from a list of findings."""
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    if not findings:
        return "low"
    return min(findings, key=lambda f: order.get(f.get("severity", "low"), 3)).get("severity", "low")


def draft_report(program: dict, findings: dict) -> dict:
    """Create a structured vulnerability report from recon findings."""
    finding_list: list[dict] = findings.get("findings", [])
    if not finding_list:
        return {}

    severity = _severity_for_findings(finding_list)
    base_url = findings.get("base_url", "unknown")
    prog_name = program.get("name", findings.get("program", "Unknown Program"))

    # Build title from the highest-severity finding
    top_finding = min(
        finding_list,
        key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(f.get("severity", "low"), 3),
    )
    finding_type = top_finding.get("type", "security_misconfiguration")
    human_type = finding_type.replace("_", " ").title()

    title = f"{human_type} in {prog_name}"

    steps: list[str] = [
        f"1. Navigate to {base_url}",
        "2. Open browser developer tools (F12) → Network tab",
        "3. Reload the page and inspect response headers",
    ]
    for i, f in enumerate(finding_list[:5], start=4):
        steps.append(f"{i}. Observe: {f.get('detail', f.get('type'))}")

    steps_text = "\n".join(steps)

    impact_map = {
        "critical": "An attacker can gain unauthorized administrative access, potentially leading to full system compromise.",
        "high": "An attacker can exploit this issue to steal session tokens, perform cross-site request forgery, or access sensitive data.",
        "medium": "An attacker can abuse this to conduct phishing, clickjacking, or information disclosure attacks.",
        "low": "This misconfiguration increases the attack surface and may assist an attacker in chaining additional vulnerabilities.",
    }

    recommendation_map = {
        "cors_wildcard": "Restrict Access-Control-Allow-Origin to explicitly trusted origins. Avoid using wildcard '*' on endpoints that handle authenticated data.",
        "missing_csp": "Implement a Content-Security-Policy header with appropriate directives to prevent XSS and data injection attacks.",
        "exposed_admin": "Restrict access to administrative endpoints via network-level controls (VPN, IP allowlist) or remove from public internet exposure.",
        "exposed_git": "Remove the .git directory from the web root immediately. Rotate all credentials and secrets that may be exposed in git history.",
        "exposed_swagger": "Restrict API documentation endpoints to authenticated users or internal networks only.",
        "exposed_api": "Ensure API endpoints require authentication and are not accessible without valid credentials.",
        "missing_hsts": "Add Strict-Transport-Security: max-age=31536000; includeSubDomains; preload to enforce HTTPS.",
        "missing_x_frame": "Add X-Frame-Options: DENY or SAMEORIGIN to prevent clickjacking attacks.",
        "missing_x_content_type": "Add X-Content-Type-Options: nosniff to prevent MIME type sniffing.",
        "missing_referrer_policy": "Add Referrer-Policy: strict-origin-when-cross-origin to limit referrer information leakage.",
    }

    recommendations: list[str] = []
    seen_types: set[str] = set()
    for f in finding_list:
        ftype = f.get("type", "")
        if ftype not in seen_types and ftype in recommendation_map:
            recommendations.append(f"- **{ftype.replace('_', ' ').title()}**: {recommendation_map[ftype]}")
            seen_types.add(ftype)

    findings_summary = "\n".join(
        f"| {f.get('type', '')} | {f.get('severity', '')} | {f.get('url', '')} | {f.get('detail', '')} |"
        for f in finding_list
    )

    return {
        "id": str(uuid.uuid4()),
        "platform": program.get("platform", "hackerone"),
        "program": program.get("handle", ""),
        "program_name": prog_name,
        "title": title,
        "severity": severity,
        "steps_to_reproduce": steps_text,
        "impact": impact_map.get(severity, impact_map["low"]),
        "recommendation": "\n".join(recommendations) if recommendations else recommendation_map.get(finding_type, ""),
        "findings_table": f"| Type | Severity | URL | Detail |\n|---|---|---|---|\n{findings_summary}",
        "findings": finding_list,
        "base_url": base_url,
        "drafted_at": datetime.utcnow().isoformat() + "Z",
    }


# ── API submission ────────────────────────────────────────────────────────────

async def submit_report_api(report: dict, platform: str) -> dict:
    """
    Attempt to submit a report via the platform's API.
    Returns {"ok": True/False, "report_id": ..., "error": ...}
    """
    platform = platform.lower()

    if platform == "hackerone":
        if not H1_TOKEN or not H1_USER:
            return {"ok": False, "error": "HackerOne credentials not set"}
        try:
            payload = {
                "data": {
                    "type": "report",
                    "attributes": {
                        "title": report["title"],
                        "vulnerability_information": (
                            f"## Steps to Reproduce\n{report['steps_to_reproduce']}\n\n"
                            f"## Impact\n{report['impact']}\n\n"
                            f"## Recommendation\n{report['recommendation']}\n\n"
                            f"## Findings\n{report['findings_table']}"
                        ),
                        "severity_rating": report["severity"],
                        "impact": report["impact"],
                    },
                    "relationships": {
                        "program": {
                            "data": {"type": "program", "attributes": {"handle": report["program"]}}
                        }
                    },
                }
            }
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.post(
                    "https://api.hackerone.com/v1/hackers/reports",
                    auth=(H1_USER, H1_TOKEN),  # NOSONAR - credentials from env vars
                    json=payload,
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                )
                if r.status_code in (200, 201):
                    data = r.json()
                    report_id = data.get("data", {}).get("id", "unknown")
                    return {"ok": True, "platform": "hackerone", "report_id": report_id}
                return {
                    "ok": False,
                    "platform": "hackerone",
                    "error": f"HTTP {r.status_code}: {r.text[:200]}",
                }
        except Exception as e:
            return {"ok": False, "platform": "hackerone", "error": str(e)}

    if platform == "intigriti":
        if not INTIGRITI_TOKEN:
            return {"ok": False, "error": "INTIGRITI_TOKEN not set"}
        try:
            payload = {
                "title": report["title"],
                "description": (
                    f"## Steps to Reproduce\n{report['steps_to_reproduce']}\n\n"
                    f"## Impact\n{report['impact']}\n\n"
                    f"## Recommendation\n{report['recommendation']}"
                ),
                "severity": {"id": report["severity"]},
            }
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.post(
                    f"https://api.intigriti.com/external/researcher/v1/programs/{report['program']}/submissions",
                    headers={"Authorization": f"Bearer {INTIGRITI_TOKEN}", "Accept": "application/json"},
                    json=payload,
                )
                if r.status_code in (200, 201):
                    data = r.json()
                    return {"ok": True, "platform": "intigriti", "report_id": data.get("id", "unknown")}
                return {
                    "ok": False,
                    "platform": "intigriti",
                    "error": f"HTTP {r.status_code}: {r.text[:200]}",
                }
        except Exception as e:
            return {"ok": False, "platform": "intigriti", "error": str(e)}

    if platform == "yeswehack":
        if not YWH_TOKEN:
            return {"ok": False, "error": "YESWEHACK_TOKEN not set"}
        try:
            payload = {
                "title": report["title"],
                "scope": report.get("base_url", ""),
                "impact": report["impact"],
                "description": (
                    f"## Steps to Reproduce\n{report['steps_to_reproduce']}\n\n"
                    f"## Impact\n{report['impact']}\n\n"
                    f"## Recommendation\n{report['recommendation']}"
                ),
                "cvss_vector": "",
            }
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.post(
                    f"https://api.yeswehack.com/programs/{report['program']}/reports",
                    headers={"Authorization": f"Bearer {YWH_TOKEN}", "Accept": "application/json"},
                    json=payload,
                )
                if r.status_code in (200, 201):
                    data = r.json()
                    return {"ok": True, "platform": "yeswehack", "report_id": data.get("id", "unknown")}
                return {
                    "ok": False,
                    "platform": "yeswehack",
                    "error": f"HTTP {r.status_code}: {r.text[:200]}",
                }
        except Exception as e:
            return {"ok": False, "platform": "yeswehack", "error": str(e)}

    return {"ok": False, "error": f"Unknown platform: {platform}"}


# ── Approval queue (SQLite) ────────────────────────────────────────────────────

def submit_via_queue(report: dict) -> dict:
    """Store a report in the pending_reports SQLite table with status='pending'."""
    _ensure_db()
    report_id = report.get("id") or str(uuid.uuid4())
    try:
        con = sqlite3.connect(str(DB_PATH))
        con.execute(
            """
            INSERT OR REPLACE INTO pending_reports
                (id, platform, program, title, severity, findings_json, status, created_at, notified_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, NULL)
            """,
            (
                report_id,
                report.get("platform", "unknown"),
                report.get("program", "unknown"),
                report.get("title", "Untitled"),
                report.get("severity", "low"),
                json.dumps(report),
                time.time(),
            ),
        )
        con.commit()
        con.close()
        return {"ok": True, "queued_id": report_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_queued_reports() -> list[dict]:
    """Return all pending reports from SQLite."""
    _ensure_db()
    try:
        con = sqlite3.connect(str(DB_PATH))
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM pending_reports ORDER BY created_at DESC").fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


# ── Pipeline run state ────────────────────────────────────────────────────────

_last_run: dict[str, Any] = {}


def get_last_run() -> dict:
    return _last_run.copy()


def _save_run(run: dict) -> None:
    _ensure_db()
    try:
        con = sqlite3.connect(str(DB_PATH))
        con.execute(
            """
            INSERT OR REPLACE INTO pipeline_runs
                (id, started_at, finished_at, identified, executed, submitted, queued, summary_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run["id"],
                run.get("started_at", 0),
                run.get("finished_at"),
                run.get("identified", 0),
                run.get("executed", 0),
                run.get("submitted", 0),
                run.get("queued", 0),
                json.dumps(run),
            ),
        )
        con.commit()
        con.close()
    except Exception:
        pass


# ── Full pipeline orchestration ───────────────────────────────────────────────

async def run_pipeline(
    platforms: list[str] | None = None,
    top_n: int = 5,
) -> dict[str, Any]:
    """
    Full async pipeline:
      1. Identify top programs
      2. Parallel recon on each
      3. For each finding, try API submit → queue on failure
      4. Return summary
    """
    global _last_run
    if platforms is None:
        platforms = ["hackerone", "intigriti", "yeswehack"]

    run_id = str(uuid.uuid4())
    run: dict[str, Any] = {
        "id": run_id,
        "started_at": time.time(),
        "finished_at": None,
        "platforms": platforms,
        "identified": 0,
        "executed": 0,
        "submitted": 0,
        "queued": 0,
        "reports": [],
        "errors": [],
    }

    # Step 1: Identify
    try:
        programs = await identify_opportunities(platforms=platforms, top_n=top_n)
        run["identified"] = len(programs)
    except Exception as e:
        run["errors"].append(f"identify_opportunities: {e}")
        programs = []

    # Step 2: Parallel recon
    recon_tasks = [execute_recon(prog) for prog in programs]
    recon_results = await asyncio.gather(*recon_tasks, return_exceptions=True)
    run["executed"] = len(programs)

    # Step 3: Draft + submit
    for prog, recon in zip(programs, recon_results):
        if isinstance(recon, Exception):
            run["errors"].append(f"recon({prog.get('handle')}): {recon}")
            continue

        if not recon.get("findings"):
            continue

        report = draft_report(prog, recon)
        if not report:
            continue

        platform = prog.get("platform", "hackerone")
        submit_result = await submit_report_api(report, platform)

        if submit_result.get("ok"):
            run["submitted"] += 1
            run["reports"].append({
                "program": prog.get("name"),
                "platform": platform,
                "title": report["title"],
                "severity": report["severity"],
                "action": "submitted",
                "report_id": submit_result.get("report_id"),
            })
        else:
            queue_result = submit_via_queue(report)
            if queue_result.get("ok"):
                run["queued"] += 1
                run["reports"].append({
                    "program": prog.get("name"),
                    "platform": platform,
                    "title": report["title"],
                    "severity": report["severity"],
                    "action": "queued",
                    "queued_id": queue_result.get("queued_id"),
                    "submit_error": submit_result.get("error"),
                })
            else:
                run["errors"].append(
                    f"queue({prog.get('handle')}): {queue_result.get('error')}"
                )

    run["finished_at"] = time.time()
    _last_run = run
    _save_run(run)
    return run
