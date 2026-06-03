from __future__ import annotations
import subprocess
import shlex
from backend.app.core.config import settings

BLOCKED_PATTERNS = [
    "rm -rf /",
    "mkfs",
    "shutdown",
    "reboot",
    ":(){",
    "dd if=",
    "chmod -R 777 /",
    "chown -R",
    "iptables -F",
    "ufw disable",
]

def validate_command(command: str) -> tuple[bool, str]:
    if not settings.allow_terminal:
        return False, "Terminal execution disabled by SUPREME_ALLOW_TERMINAL=false."
    if not command.strip():
        return False, "Empty command."
    for pattern in BLOCKED_PATTERNS:
        if pattern in command:
            return False, f"Blocked dangerous command pattern: {pattern}"
    return True, "ok"

def execute(command: str, timeout: int = 120) -> dict:
    ok, reason = validate_command(command)
    if not ok:
        return {"command": command, "returncode": 126, "stdout": "", "stderr": reason}
    proc = subprocess.run(
        command,
        shell=True,
        cwd=settings.workspace_dir,
        capture_output=True,
        text=True,
        timeout=max(5, min(timeout, 300)),
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-20000:],
        "stderr": proc.stderr[-20000:],
    }
