"""Sandboxed python execution via subprocess with limits."""
import asyncio, tempfile, os
async def run_sandboxed(source: str):
    if any(b in source for b in ["import os","subprocess","socket","__import__"]):
        return {"error":"disallowed import"}
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(source); path = f.name
    try:
        proc = await asyncio.create_subprocess_exec(
            "python","-I","-S", path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=10)
        except asyncio.TimeoutError:
            proc.kill(); return {"error":"timeout"}
        return {"stdout": out.decode()[:4000], "stderr": err.decode()[:2000]}
    finally:
        os.unlink(path)
