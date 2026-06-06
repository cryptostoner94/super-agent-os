import os, httpx
TOK = os.getenv("BUFFER_ACCESS_TOKEN","")
BASE = "https://api.bufferapp.com/1"

async def schedule(payload: str):
    import json
    d = json.loads(payload)
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/updates/create.json",
            params={"access_token": TOK},
            data={"text": d["text"], "profile_ids[]": d.get("profiles",[])})
        return r.json()
