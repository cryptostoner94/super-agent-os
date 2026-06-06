"""
IDENTITY
========
Cryptographic and logical self-definition of the system.

Responsibilities
----------------
* Maintain an immutable, signature-verifiable identity card.
* Hardcode immutable system boundaries and operational objectives.
* Provide tamper detection so other modules can refuse to start under drift.

The signing scheme uses HMAC-SHA256 over a deterministic JSON canonicalization
of the identity payload. The secret is derived from a machine-local entropy
file written on first run (zero external dependencies).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Immutable, hardcoded operational charter. Editing any of these constants
# is treated as a *new* identity (a fresh hash is computed).
_IMMUTABLE_OBJECTIVES: Tuple[str, ...] = (
    "Operate as a fully autonomous, self-hosted agent runtime.",
    "Preserve user intent across every transformation.",
    "Never escalate privileges beyond declared environmental boundaries.",
    "Prefer zero-cost, zero-key, deterministic execution paths.",
    "Surface every error to the user; never silently degrade safety.",
)

_IMMUTABLE_BOUNDARIES: Tuple[str, ...] = (
    "no_external_paid_apis",
    "no_outbound_credential_exfiltration",
    "no_self_rewriting_outside_skills_dir",
    "no_unbounded_parallelism",
    "no_silent_user_data_deletion",
)

_SYSTEM_NAME = "Ultimate Autonomous Core"
_SYSTEM_CODE = "UAC"
_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class IdentityCard:
    system_name: str
    system_code: str
    schema_version: int
    instance_id: str
    created_at: float
    objectives: Tuple[str, ...]
    boundaries: Tuple[str, ...]
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["objectives"] = list(self.objectives)
        d["boundaries"] = list(self.boundaries)
        return d


class IdentityError(RuntimeError):
    """Raised on any identity validation failure (drift, tamper, corruption)."""


class Identity:
    """Manages the identity card lifecycle (create / load / verify)."""

    CARD_FILE = "identity_card.json"
    SECRET_FILE = "identity_secret.bin"

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._card_path = self.state_dir / self.CARD_FILE
        self._secret_path = self.state_dir / self.SECRET_FILE

    # --------------------------- public API ------------------------------- #

    def load_or_create(self) -> IdentityCard:
        if self._card_path.exists() and self._secret_path.exists():
            card = self._load()
            self.verify(card)  # raises on tamper
            return card
        return self._create_fresh()

    def verify(self, card: IdentityCard) -> bool:
        expected = self._sign(self._canonical_payload(card))
        if not hmac.compare_digest(expected, card.signature):
            raise IdentityError(
                "Identity signature mismatch — possible tampering or drift."
            )
        # Reject identities whose hardcoded charter has changed.
        if tuple(card.objectives) != _IMMUTABLE_OBJECTIVES:
            raise IdentityError("Objectives drift detected.")
        if tuple(card.boundaries) != _IMMUTABLE_BOUNDARIES:
            raise IdentityError("Boundary drift detected.")
        return True

    def fingerprint(self, card: IdentityCard) -> str:
        """Short, stable visual hash for logs/dashboards."""
        h = hashlib.sha256(card.signature.encode()).hexdigest()
        return f"{h[:4]}-{h[4:8]}-{h[8:12]}"

    # --------------------------- internals -------------------------------- #

    def _create_fresh(self) -> IdentityCard:
        secret = secrets.token_bytes(32)
        self._secret_path.write_bytes(secret)
        if os.name == "posix":
            try:
                os.chmod(self._secret_path, 0o600)
            except OSError:
                pass

        instance_id = hashlib.sha256(secret + str(time.time_ns()).encode()).hexdigest()[:16]
        payload_card = IdentityCard(
            system_name=_SYSTEM_NAME,
            system_code=_SYSTEM_CODE,
            schema_version=_SCHEMA_VERSION,
            instance_id=instance_id,
            created_at=time.time(),
            objectives=_IMMUTABLE_OBJECTIVES,
            boundaries=_IMMUTABLE_BOUNDARIES,
            signature="",  # filled below
        )
        sig = self._sign(self._canonical_payload(payload_card))
        card = IdentityCard(**{**payload_card.to_dict(), "signature": sig,
                               "objectives": _IMMUTABLE_OBJECTIVES,
                               "boundaries": _IMMUTABLE_BOUNDARIES})
        self._card_path.write_text(json.dumps(card.to_dict(), indent=2, sort_keys=True))
        return card

    def _load(self) -> IdentityCard:
        try:
            raw = json.loads(self._card_path.read_text())
            return IdentityCard(
                system_name=raw["system_name"],
                system_code=raw["system_code"],
                schema_version=int(raw["schema_version"]),
                instance_id=raw["instance_id"],
                created_at=float(raw["created_at"]),
                objectives=tuple(raw["objectives"]),
                boundaries=tuple(raw["boundaries"]),
                signature=raw["signature"],
            )
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            raise IdentityError(f"Corrupted identity card: {exc}") from exc

    def _canonical_payload(self, card: IdentityCard) -> bytes:
        body = {
            "system_name": card.system_name,
            "system_code": card.system_code,
            "schema_version": card.schema_version,
            "instance_id": card.instance_id,
            "created_at": card.created_at,
            "objectives": list(card.objectives),
            "boundaries": list(card.boundaries),
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()

    def _sign(self, payload: bytes) -> str:
        secret = self._secret_path.read_bytes()
        return hmac.new(secret, payload, hashlib.sha256).hexdigest()
