import asyncio, json
from fastapi import WebSocket

class Hub:
    def __init__(self):
        self.clients: set[WebSocket] = set()
        self.lock = asyncio.Lock()
    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self.lock: self.clients.add(ws)
        try:
            import time
            await ws.send_text(json.dumps({"type": "connected", "data": {"time": time.time()}}))
        except Exception:
            pass
    def disconnect(self, ws: WebSocket):
        self.clients.discard(ws)
    async def broadcast(self, msg: dict):
        dead = []
        for ws in list(self.clients):
            try: await ws.send_text(json.dumps(msg, default=str))
            except Exception: dead.append(ws)
        for d in dead: self.disconnect(d)

hub = Hub()