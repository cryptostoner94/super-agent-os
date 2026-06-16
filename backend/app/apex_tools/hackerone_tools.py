"""HackerOne API client — real public API at https://api.hackerone.com/v1/"""
import os, httpx
BASE = "https://api.hackerone.com/v1"

def _auth():
    return (os.getenv("HACKERONE_API_USERNAME",""), os.getenv("HACKERONE_API_TOKEN",""))

async def list_programs(_=""):
    async with httpx.AsyncClient(auth=_auth(), timeout=30) as c:
        r = await c.get(f"{BASE}/hackers/programs")
        r.raise_for_status()
        return r.json()

async def get_program(handle: str):
    async with httpx.AsyncClient(auth=_auth(), timeout=30) as c:
        r = await c.get(f"{BASE}/hackers/programs/{handle}")
        return r.json()

async def list_my_reports(_=""):
    async with httpx.AsyncClient(auth=_auth(), timeout=30) as c:
        r = await c.get(f"{BASE}/hackers/me/reports")
        return r.json()

async def submit_report(payload: str):
    import json
    data = json.loads(payload) if isinstance(payload, str) else payload
    async with httpx.AsyncClient(auth=_auth(), timeout=30) as c:
        r = await c.post(f"{BASE}/hackers/reports", json={"data": {"type":"report","attributes": data}})
        return r.json()
