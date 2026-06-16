"""
JSON state store — library, projects, tasks, runs.

First run: if state.json doesn't exist it is created from
config/templates/state.json (committed safe template).
All writes go to data/state.json which is gitignored.
"""
from __future__ import annotations
import json
from pathlib import Path
from backend.app.core.config import settings

STATE = Path(settings.workspace_dir) / "state.json"
_TEMPLATE = Path(__file__).resolve().parents[4] / "config" / "templates" / "state.json"

_FALLBACK: dict = {"library": [], "projects": [], "tasks": [], "runs": []}


def _init_state() -> dict:
    """Return default state from template, or built-in fallback."""
    if _TEMPLATE.exists():
        try:
            return json.loads(_TEMPLATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return _FALLBACK.copy()


def load_state() -> dict:
    if not STATE.exists():
        save_state(_init_state())
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        default = _init_state()
        save_state(default)
        return default


def save_state(data: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_library(item: dict) -> dict:
    state = load_state()
    state.setdefault("library", []).insert(0, item)
    save_state(state)
    return item
