import os, httpx
KEY = os.getenv("SENDGRID_API_KEY","")

UNSUB = '\n\n---\nUnsubscribe: https://example.com/unsubscribe?e={email}'  # CAN-SPAM

async def send(payload: str):
    import json
    d = json.loads(payload)
    body = d["text"] + UNSUB.format(email=d["to"])
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post("https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {KEY}"},
            json={
                "personalizations":[{"to":[{"email": d["to"]}]}],
                "from": {"email": d.get("from","bot@apex.local")},
                "subject": d["subject"],
                "content": [{"type":"text/plain","value": body}],
            })
        return {"status_code": r.status_code}

async def send_invoice(payload: str): return await send(payload)
