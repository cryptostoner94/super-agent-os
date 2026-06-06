import httpx
async def search(q: str):
    # use DuckDuckGo HTML (no key); swap to SerpAPI/Brave for prod
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
        r = await c.get("https://duckduckgo.com/html/", params={"q": q},
                        headers={"User-Agent":"Mozilla/5.0"})
        return {"html": r.text[:8000]}

async def fetch(url: str):
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
        r = await c.get(url, headers={"User-Agent":"APEX-Agent/0.1"})
        return {"status": r.status_code, "text": r.text[:8000]}
