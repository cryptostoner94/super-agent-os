import os, httpx
KEY = os.getenv("APOLLO_API_KEY","")
BASE = "https://api.apollo.io/v1"

async def search_people(query: str):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/mixed_people/search",
            json={"api_key": KEY, "q_keywords": query, "page":1, "per_page":10})
        return r.json()

async def enrich(email: str):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/people/match", json={"api_key": KEY, "email": email})
        return r.json()
