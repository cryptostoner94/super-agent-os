import httpx, json as _json
async def request(payload: str):
    d = _json.loads(payload)
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.request(d.get("method","GET"), d["url"],
            headers=d.get("headers",{}), json=d.get("json"), params=d.get("params"))
        return {"status": r.status_code, "body": r.text[:4000]}
