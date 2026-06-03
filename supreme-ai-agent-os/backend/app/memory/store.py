from __future__ import annotations
import json
from pathlib import Path
from backend.app.core.config import settings

STATE = Path(settings.workspace_dir) / "state.json"

DEFAULT_STATE = {"library": [], "projects": [], "tasks": [], "runs": []}

def load_state() -> dict:
    if not STATE.exists():
        save_state(DEFAULT_STATE.copy())
    return json.loads(STATE.read_text(encoding="utf-8"))

def save_state(data: dict) -> None:
    STATE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def add_library(item: dict) -> dict:
    state = load_state()
    state.setdefault("library", []).insert(0, item)
    save_state(state)
    return item
