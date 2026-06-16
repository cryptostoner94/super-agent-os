import os, httpx
TOK = os.getenv("MASTODON_ACCESS_TOKEN","")
INST = os.getenv("MASTODON_INSTANCE","https://mastodon.social")

async def post(text: str):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{INST}/api/v1/statuses",
            headers={"Authorization": f"Bearer {TOK}"},
            data={"status": text})
        return r.json()
