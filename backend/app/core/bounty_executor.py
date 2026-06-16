"""
Real bounty execution engine - calls live APIs, returns real data.
"""
from __future__ import annotations
import os, asyncio
import httpx

H1_USER = os.getenv("HACKERONE_USERNAME", "")
H1_TOKEN = os.getenv("HACKERONE_API_TOKEN", "")
INTIGRITI_TOKEN = os.getenv("INTIGRITI_TOKEN", "")
YWH_TOKEN = os.getenv("YESWEHACK_TOKEN", "")


async def h1_get_profile() -> dict:
    if not H1_TOKEN or not H1_USER:
        return {"ok": False, "error": "HackerOne credentials not set", "profile": {}}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(
                "https://api.hackerone.com/v1/hackers/me",
                auth=(H1_USER, H1_TOKEN),  # NOSONAR - credentials from env vars
                headers={"Accept": "application/json"},
            )
            r.raise_for_status()
            data = r.json()
            attr = data.get("data", {}).get("attributes", {})
            return {"ok": True, "source": "hackerone", "profile": attr}
    except Exception as e:
        return {"ok": False, "error": str(e), "source": "hackerone", "profile": {}}


async def h1_list_programs(max_results: int = 20) -> dict:
    if not H1_TOKEN or not H1_USER:
        return {"ok": False, "error": "HackerOne credentials not set", "programs": []}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(
                "https://api.hackerone.com/v1/hackers/programs",
                auth=(H1_USER, H1_TOKEN),  # NOSONAR - credentials from env vars
                params={"page[size]": max_results, "sort": "-started_accepting_at"},
                headers={"Accept": "application/json"},
            )
            r.raise_for_status()
            data = r.json()
            programs = []
            for p in data.get("data", []):
                attr = p.get("attributes", {})
                programs.append({
                    "id": p.get("id"),
                    "handle": attr.get("handle"),
                    "name": attr.get("name"),
                    "url": "https://hackerone.com/" + str(attr.get("handle", "")),
                    "offers_bounties": attr.get("offers_bounties"),
                    "submission_state": attr.get("submission_state"),
                    "min_bounty": attr.get("min_bounty_table_value"),
                    "max_bounty": attr.get("max_bounty_table_value"),
                    "response_efficiency": attr.get("response_efficiency_percentage"),
                    "resolved_reports": attr.get("resolved_report_count"),
                })
            return {"ok": True, "source": "hackerone", "count": len(programs), "programs": programs}
    except Exception as e:
        return {"ok": False, "error": str(e), "source": "hackerone", "programs": []}


async def h1_my_reports() -> dict:
    if not H1_TOKEN or not H1_USER:
        return {"ok": False, "error": "HackerOne credentials not set", "reports": []}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(
                "https://api.hackerone.com/v1/hackers/me/reports",
                auth=(H1_USER, H1_TOKEN),  # NOSONAR - credentials from env vars
                headers={"Accept": "application/json"},
            )
            r.raise_for_status()
            data = r.json()
            reports = []
            for rep in data.get("data", []):
                attr = rep.get("attributes", {})
                reports.append({
                    "id": rep.get("id"),
                    "title": attr.get("title"),
                    "state": attr.get("state"),
                    "created_at": attr.get("created_at"),
                    "bounty": attr.get("bounty_amount"),
                })
            return {"ok": True, "source": "hackerone", "count": len(reports), "reports": reports}
    except Exception as e:
        return {"ok": False, "error": str(e), "source": "hackerone", "reports": []}


async def intigriti_list_programs() -> dict:
    if not INTIGRITI_TOKEN:
        return {"ok": False, "error": "INTIGRITI_TOKEN not set", "programs": []}
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                "https://api.intigriti.com/external/researcher/v1/programs",
                headers={
                    "Authorization": "Bearer " + INTIGRITI_TOKEN,
                    "Accept": "application/json",
                },
            )
            r.raise_for_status()
            data = r.json()
            records = data.get("records", [])
            total = data.get("maxCount", len(records))
            programs = []
            for p in records:
                max_b = p.get("maxBounty") or {}
                min_b = p.get("minBounty") or {}
                handle = p.get("handle") or p.get("id", "")
                programs.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "handle": handle,
                    "url": "https://app.intigriti.com/researcher/programs/" + str(handle),
                    "status": p.get("status"),
                    "min_bounty": str(min_b.get("value", 0)) + " " + str(min_b.get("currency", "")).strip(),
                    "max_bounty": str(max_b.get("value", 0)) + " " + str(max_b.get("currency", "")).strip(),
                    "confidentiality_level": p.get("confidentialityLevel"),
                    "following": p.get("following"),
                })
            return {"ok": True, "source": "intigriti", "total": total, "count": len(programs), "programs": programs}
    except Exception as e:
        return {"ok": False, "error": str(e), "source": "intigriti", "programs": []}


async def intigriti_my_submissions() -> dict:
    if not INTIGRITI_TOKEN:
        return {"ok": False, "error": "INTIGRITI_TOKEN not set", "submissions": []}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(
                "https://api.intigriti.com/external/researcher/v1/submissions",
                headers={
                    "Authorization": "Bearer " + INTIGRITI_TOKEN,
                    "Accept": "application/json",
                },
            )
            r.raise_for_status()
            data = r.json()
            records = data.get("records", data if isinstance(data, list) else [])
            submissions = []
            for s in records:
                submissions.append({
                    "id": s.get("id"),
                    "title": s.get("title"),
                    "status": s.get("status"),
                    "severity": s.get("severity"),
                    "created_at": s.get("createdAt"),
                    "program": s.get("program", {}).get("name"),
                })
            return {"ok": True, "source": "intigriti", "count": len(submissions), "submissions": submissions}
    except Exception as e:
        return {"ok": False, "error": str(e), "source": "intigriti", "submissions": []}


async def ywh_list_programs() -> dict:
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            headers = {}
            if YWH_TOKEN:
                headers["Authorization"] = "Bearer " + YWH_TOKEN
            r = await c.get("https://api.yeswehack.com/programs", headers=headers)
            r.raise_for_status()
            data = r.json()
            items = data.get("items", data if isinstance(data, list) else [])
            programs = []
            for p in items[:50]:
                programs.append({
                    "slug": p.get("slug"),
                    "name": p.get("title") or p.get("name"),
                    "url": "https://yeswehack.com/programs/" + str(p.get("slug", "")),
                    "bounty": p.get("bounty"),
                    "vdp": p.get("vdp"),
                    "status": p.get("status"),
                    "max_bounty": p.get("max_bounty"),
                })
            return {"ok": True, "source": "yeswehack", "count": len(programs), "programs": programs}
    except Exception as e:
        return {"ok": False, "error": str(e), "source": "yeswehack", "programs": []}


async def execute_bounty_hunt(action: str = "list_programs", platform: str = "all") -> dict:
    results = {}
    if action == "list_programs":
        tasks = []
        if platform in ("all", "hackerone"):
            tasks.append(("hackerone", h1_list_programs()))
        if platform in ("all", "intigriti"):
            tasks.append(("intigriti", intigriti_list_programs()))
        if platform in ("all", "yeswehack"):
            tasks.append(("yeswehack", ywh_list_programs()))
        gathered = await asyncio.gather(*[coro for _, coro in tasks], return_exceptions=True)
        for i, (name, _) in enumerate(tasks):
            r = gathered[i]
            results[name] = r if not isinstance(r, Exception) else {"ok": False, "error": str(r)}
    elif action == "my_profile":
        results["hackerone"] = await h1_get_profile()
    elif action == "my_reports":
        h1r, intir = await asyncio.gather(h1_my_reports(), intigriti_my_submissions())
        results["hackerone"] = h1r
        results["intigriti"] = intir
    elif action == "dashboard":
        profile, p_h1, p_inti, p_ywh, reports = await asyncio.gather(
            h1_get_profile(), h1_list_programs(10),
            intigriti_list_programs(), ywh_list_programs(), h1_my_reports(),
            return_exceptions=True,
        )
        def safe(v):
            return v if not isinstance(v, Exception) else {"ok": False, "error": str(v)}
        p_h1, p_inti, p_ywh = safe(p_h1), safe(p_inti), safe(p_ywh)
        reports, profile = safe(reports), safe(profile)
        results = {
            "profile": profile,
            "open_programs": {
                "hackerone": p_h1.get("programs", [])[:5],
                "intigriti": p_inti.get("programs", [])[:5],
                "yeswehack": p_ywh.get("programs", [])[:5],
            },
            "my_reports": reports.get("reports", []),
            "summary": {
                "h1_programs": p_h1.get("count", 0),
                "intigriti_programs": p_inti.get("total", p_inti.get("count", 0)),
                "ywh_programs": p_ywh.get("count", 0),
                "my_h1_reports": reports.get("count", 0),
            }
        }
    return {"action": action, "platform": platform, "results": results}
