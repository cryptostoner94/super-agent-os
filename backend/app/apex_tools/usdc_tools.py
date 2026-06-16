"""Circle USDC — sandbox by default. Docs: https://developers.circle.com/"""
import os, httpx
BASE = "https://api-sandbox.circle.com/v1" if os.getenv("CIRCLE_ENV","sandbox")=="sandbox" else "https://api.circle.com/v1"
HEADERS = {"Authorization": f"Bearer {os.getenv('CIRCLE_API_KEY','')}"}

async def balance(_=""):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"{BASE}/businessAccount/balances", headers=HEADERS)
        return r.json()

async def transfer(payload: str):
    import json
    d = json.loads(payload)
    if d.get("amount_usd",0) > float(os.getenv("WARDEN_APPROVAL_THRESHOLD","100")):
        return {"error":"requires_human_approval"}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/businessAccount/transfers", headers=HEADERS, json=d)
        return r.json()
