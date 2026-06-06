import os, httpx
KEY = os.getenv("HUNTER_API_KEY","")
BASE = "https://api.hunter.io/v2"

async def find_email(payload: str):
    import json
    d = json.loads(payload) if payload.startswith("{") else {"domain": payload}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"{BASE}/email-finder", params={**d, "api_key": KEY})
        return r.json()

async def verify(email: str):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"{BASE}/email-verifier", params={"email": email, "api_key": KEY})
        return r.json()
