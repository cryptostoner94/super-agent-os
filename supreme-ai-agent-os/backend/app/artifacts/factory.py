from __future__ import annotations
from pathlib import Path
import csv
import io
import time
import pandas as pd
from backend.app.core.config import settings

ARTIFACT_DIR = Path(settings.workspace_dir) / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

def _name(prefix: str, ext: str) -> Path:
    return ARTIFACT_DIR / f"{prefix}_{int(time.time())}.{ext}"

def create_markdown(title: str, content: str) -> dict:
    path = _name("document", "md")
    path.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")
    return {"type": "markdown", "path": str(path)}

def create_html(title: str, body: str) -> dict:
    path = _name("website", "html")
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:Arial;padding:48px;background:#f6f7fb}}main{{background:white;border-radius:24px;padding:32px;max-width:920px;margin:auto;box-shadow:0 10px 30px rgba(0,0,0,.08)}}</style></head>
<body><main><h1>{title}</h1><p>{body}</p></main></body></html>"""
    path.write_text(html, encoding="utf-8")
    return {"type": "html", "path": str(path), "html": html}

def create_xlsx(raw: str) -> dict:
    path = _name("spreadsheet", "xlsx")
    try:
        df = pd.read_csv(io.StringIO(raw))
    except Exception:
        df = pd.DataFrame({"content": raw.splitlines() or [""]})
    df.to_excel(path, index=False)
    return {"type": "xlsx", "path": str(path), "rows": len(df), "columns": list(df.columns)}

def create_csv(raw: str) -> dict:
    path = _name("data", "csv")
    path.write_text(raw, encoding="utf-8")
    return {"type": "csv", "path": str(path)}
