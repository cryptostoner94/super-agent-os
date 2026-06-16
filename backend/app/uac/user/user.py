"""
USER
====
Contextual gateway.

Wraps user-supplied constraints + environmental boundaries into a safe
execution profile every other module reads (read-only).

A `UserProfile` is loaded from `<state>/user_profile.json` (if present) or
created with sane defaults. Constraints are *additive* against the
hardcoded IDENTITY boundaries — they can never weaken safety.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class ConstraintError(RuntimeError):
    """Raised when an action violates the active user profile."""


@dataclass
class UserProfile:
    user_id: str
    display_name: str = "operator"
    created_at: float = field(default_factory=time.time)
    # additive deny-list, on top of IDENTITY immutable boundaries
    extra_forbidden_skills: List[str] = field(default_factory=list)
    # caps that the runtime must respect
    max_parallel_override: Optional[int] = None
    network_enabled: bool = True
    artifact_quota_mb_override: Optional[int] = None
    # arbitrary metadata
    tags: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class User:
    """Loads / persists / enforces the active user profile."""

    PROFILE_FILE = "user_profile.json"

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._path = self.state_dir / self.PROFILE_FILE

    def load_or_create(self, user_id: str = "local-operator") -> UserProfile:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text())
                return UserProfile(**raw)
            except Exception:
                pass  # fall through to fresh
        profile = UserProfile(user_id=user_id)
        self.save(profile)
        return profile

    def save(self, profile: UserProfile) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(profile.to_dict(), indent=2, sort_keys=True))
        tmp.replace(self._path)

    # -------------------------- enforcement ------------------------------- #

    def enforce_skill_allowed(self, profile: UserProfile, skill_name: str) -> None:
        if skill_name in set(profile.extra_forbidden_skills):
            raise ConstraintError(f"skill blocked by user profile: {skill_name}")

    def effective_limits(
        self,
        profile: UserProfile,
        base_limits: Dict[str, Any],
    ) -> Dict[str, Any]:
        out = dict(base_limits)
        if profile.max_parallel_override is not None:
            out["max_parallel_tasks"] = min(
                int(profile.max_parallel_override),
                int(base_limits.get("max_parallel_tasks", 15)),
            )
        if profile.artifact_quota_mb_override is not None:
            out["artifact_quota_mb"] = min(
                int(profile.artifact_quota_mb_override),
                int(base_limits.get("artifact_quota_mb", 4096)),
            )
        out["network_enabled"] = bool(profile.network_enabled)
        return out
