import os, httpx
TOK = os.getenv("TELEGRAM_BOT_TOKEN",""); CHAT = os.getenv("TELEGRAM_CHAT_ID","")
async def alert(text: str):
    if not TOK: return {"skipped":"no token"}
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"https://api.telegram.org/bot{TOK}/sendMessage",
            json={"chat_id": CHAT, "text": text[:4000]})
        return r.json()
