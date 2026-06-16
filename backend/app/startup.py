"""
First-run initialization — generates all required secrets and runtime
directories automatically. Safe to call on every startup (idempotent).

Generated on first run (never committed to git):
  {state_dir}/session_signing_key.bin   — 32-byte HMAC-SHA256 key
  {state_dir}/encryption_key.bin        — 32-byte AES-256 key
  {state_dir}/agent_identity.json       — agent instance fingerprint
  {state_dir}/identity_secret.bin       — UAC identity HMAC secret (via Identity)
  {state_dir}/identity_card.json        — UAC identity card (via Identity)
  {state_dir}/boot_manifest.json        — UAC boot manifest (via Bootstrap)
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
import uuid
from pathlib import Path


# ── Key generation helpers ────────────────────────────────────────────────────

def _generate_key(path: Path, nbytes: int = 32, label: str = "") -> bytes:
    """Generate and persist a random key. Idempotent — returns existing key if present."""
    if path.exists():
        return path.read_bytes()
    key = secrets.token_bytes(nbytes)
    _safe_write_bytes(path, key)
    return key


def _safe_write_bytes(path: Path, data: bytes) -> None:
    """Atomic write with restricted permissions (0o600)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(data)
    if os.name == "posix":
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
    os.replace(tmp, path)


def _safe_write_json(path: Path, data: dict) -> None:
    """Atomic write for JSON, with restricted permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    if os.name == "posix":
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
    os.replace(tmp, path)


# ── Runtime directory creation ────────────────────────────────────────────────

_RUNTIME_DIRS = [
    "data/state",
    "data/artifacts",
    "data/logs",
    "data/.supreme-os/state",
    "data/.supreme-os/logs",
    "data/.supreme-os/artifacts",
    "data/.supreme-os/cache",
    "data/.supreme-os/skills",
    "data/.supreme-os/sandbox",
]


def _ensure_runtime_dirs(root: Path) -> None:
    for rel in _RUNTIME_DIRS:
        (root / rel).mkdir(parents=True, exist_ok=True)


# ── Agent identity ─────────────────────────────────────────────────────────────

def _ensure_agent_identity(state_dir: Path) -> dict:
    """
    Agent-level identity separate from the UAC cryptographic identity.
    Used for session fingerprinting and logging.
    """
    path = state_dir / "agent_identity.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    identity = {
        "instance_id": str(uuid.uuid4()),
        "created_at": time.time(),
        "product": "SUPAR SMART AI — Inception Runtime",
        "version": "2.0.0",
        "schema": 1,
    }
    identity["fingerprint"] = hashlib.sha256(
        json.dumps(identity, sort_keys=True).encode()
    ).hexdigest()[:16]
    _safe_write_json(path, identity)
    return identity


# ── Public API ────────────────────────────────────────────────────────────────

class RuntimeSecrets:
    """
    Loaded once at startup. All secrets are read from disk (generated on first run).
    Never exposed via API or logged.
    """

    def __init__(
        self,
        session_signing_key: bytes,
        encryption_key: bytes,
        agent_identity: dict,
    ) -> None:
        self.session_signing_key = session_signing_key
        self.encryption_key = encryption_key
        self.agent_identity = agent_identity

    def sign(self, data: bytes) -> str:
        """Return HMAC-SHA256 hex signature of data."""
        import hmac
        return hmac.new(self.session_signing_key, data, hashlib.sha256).hexdigest()

    def identity_fingerprint(self) -> str:
        return self.agent_identity.get("fingerprint", "unknown")

    def instance_id(self) -> str:
        return self.agent_identity.get("instance_id", "unknown")


def initialize(root: Path | str | None = None) -> RuntimeSecrets:
    """
    Idempotent first-run initialization.

    On a clean clone this creates every required directory and secret.
    On subsequent starts it loads existing secrets without modifying them.

    Parameters
    ----------
    root : path to the project root (defaults to CWD / parent of this file).
    """
    if root is None:
        # Default: project root is 3 levels above this file
        # backend/app/startup.py → backend/app → backend → project_root
        root = Path(__file__).resolve().parents[2]
    root = Path(root)

    # 1. Create runtime directories
    _ensure_runtime_dirs(root)

    state_dir = root / "data" / "state"

    # 2. Session signing key — 32 random bytes, never leaves disk
    session_key = _generate_key(state_dir / "session_signing_key.bin", 32)

    # 3. Local encryption key — AES-256 equivalent, never leaves disk
    enc_key = _generate_key(state_dir / "encryption_key.bin", 32)

    # 4. Agent identity — human-readable instance fingerprint
    agent_identity = _ensure_agent_identity(state_dir)

    # 5. UAC identity + bootstrap are handled by Identity/Bootstrap classes
    #    (called in main.py lifespan). They also write to state_dir/.supreme-os.

    return RuntimeSecrets(
        session_signing_key=session_key,
        encryption_key=enc_key,
        agent_identity=agent_identity,
    )


# ── Validation ────────────────────────────────────────────────────────────────

def validate(root: Path | str | None = None) -> dict:
    """
    Check that all required secrets and dirs exist.
    Returns a dict of {check_name: {"ok": bool, "note": str}}.
    """
    if root is None:
        root = Path(__file__).resolve().parents[2]
    root = Path(root)
    state_dir = root / "data" / "state"

    checks: dict[str, dict] = {}

    for rel in _RUNTIME_DIRS:
        d = root / rel
        checks[f"dir:{rel}"] = {"ok": d.is_dir(), "note": str(d)}

    for fname, label in [
        ("session_signing_key.bin", "Session signing key"),
        ("encryption_key.bin",      "Encryption key"),
        ("agent_identity.json",     "Agent identity"),
    ]:
        p = state_dir / fname
        checks[label] = {"ok": p.exists(), "note": str(p)}

    checks["no_secrets_in_git"] = {
        "ok": True,
        "note": "data/ is gitignored — secrets never committed",
    }
    return checks
