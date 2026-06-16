"""Safe sandboxed file I/O tool."""
import os, aiofiles

SAFE_ROOT = os.getenv("APEX_WORKSPACE", "/tmp/supreme-workspace")
os.makedirs(SAFE_ROOT, exist_ok=True)

def _safe(path: str) -> str:
    full = os.path.realpath(os.path.join(SAFE_ROOT, path.lstrip("/")))
    if not full.startswith(SAFE_ROOT):
        raise ValueError("path escape")
    return full

async def read(path: str) -> dict:
    try:
        async with aiofiles.open(_safe(path), "r") as f:
            return {"content": await f.read(), "ok": True}
    except Exception as e:
        return {"error": str(e), "ok": False}

async def write(path: str, content: str = "") -> dict:
    try:
        p = _safe(path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        async with aiofiles.open(p, "w") as f:
            await f.write(content)
        return {"path": p, "ok": True}
    except Exception as e:
        return {"error": str(e), "ok": False}

async def list_dir(path: str = "") -> dict:
    try:
        entries = os.listdir(_safe(path))
        return {"entries": entries, "ok": True}
    except Exception as e:
        return {"error": str(e), "ok": False}
