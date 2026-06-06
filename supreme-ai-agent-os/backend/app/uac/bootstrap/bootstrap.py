"""
BOOTSTRAP
=========
Self-configuring entry point. Scans local environment, detects OS / hardware
limits, builds isolated working directories, persists a deterministic boot
manifest, and initializes the runtime state machine.

Design notes
------------
* Pure stdlib — no third-party imports.
* Idempotent: re-running on an existing root only refreshes the manifest.
* Single source of truth for paths (other modules consume BootContext.paths).
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict


# ----------------------------- helpers ------------------------------------ #


def _detect_cpu() -> int:
    try:
        return max(1, os.cpu_count() or 1)
    except Exception:
        return 1


def _detect_memory_mb() -> int:
    """Best-effort memory probe (Linux/macOS/Windows) without psutil."""
    try:
        if hasattr(os, "sysconf") and "SC_PAGE_SIZE" in os.sysconf_names \
                and "SC_PHYS_PAGES" in os.sysconf_names:
            page = os.sysconf("SC_PAGE_SIZE")
            pages = os.sysconf("SC_PHYS_PAGES")
            return max(256, int(page * pages / (1024 * 1024)))
    except Exception:
        pass
    try:  # Windows fallback via ctypes
        import ctypes

        class _MemStat(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = _MemStat()
        stat.dwLength = ctypes.sizeof(_MemStat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return int(stat.ullTotalPhys / (1024 * 1024))
    except Exception:
        return 1024  # conservative default


def _detect_disk_free_mb(path: Path) -> int:
    try:
        usage = shutil.disk_usage(str(path))
        return int(usage.free / (1024 * 1024))
    except Exception:
        return 1024


# ------------------------------ dataclasses ------------------------------- #


@dataclass(frozen=True)
class BootPaths:
    root: Path
    data: Path
    logs: Path
    state: Path
    artifacts: Path
    cache: Path
    skills: Path
    sandbox: Path

    def to_dict(self) -> Dict[str, str]:
        return {k: str(v) for k, v in asdict(self).items()}


@dataclass
class BootContext:
    boot_id: str
    started_at: float
    paths: BootPaths
    env: Dict[str, Any] = field(default_factory=dict)
    limits: Dict[str, Any] = field(default_factory=dict)
    manifest_path: Path = field(default_factory=lambda: Path("."))

    def summary(self) -> str:
        return (
            f"UAC boot {self.boot_id[:8]} | "
            f"py={self.env.get('python_version')} | "
            f"cpu={self.env.get('cpu_count')} | "
            f"mem={self.env.get('memory_mb')}MB | "
            f"root={self.paths.root}"
        )


# ------------------------------- Bootstrap -------------------------------- #


class Bootstrap:
    """Idempotent first-run / every-run environment initializer."""

    DEFAULT_ROOT = Path(os.environ.get("UAC_ROOT", str(Path.home() / ".uac")))
    MAX_PARALLEL_TASKS = 15  # hard ceiling per spec

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root else self.DEFAULT_ROOT

    # ----------------------------- API ------------------------------------ #

    def initialize(self) -> BootContext:
        paths = self._make_dirs()
        env = self._scan_environment()
        limits = self._derive_limits(env, paths)

        ctx = BootContext(
            boot_id=str(uuid.uuid4()),
            started_at=time.time(),
            paths=paths,
            env=env,
            limits=limits,
            manifest_path=paths.state / "boot_manifest.json",
        )
        self._write_manifest(ctx)
        return ctx

    # --------------------------- internals -------------------------------- #

    def _make_dirs(self) -> BootPaths:
        root = self.root
        paths = BootPaths(
            root=root,
            data=root / "data",
            logs=root / "logs",
            state=root / "state",
            artifacts=root / "artifacts",
            cache=root / "cache",
            skills=root / "skills",
            sandbox=root / "sandbox",
        )
        for p in paths.to_dict().values():
            Path(p).mkdir(parents=True, exist_ok=True)
        # Lock down permissions where possible (POSIX).
        if os.name == "posix":
            try:
                os.chmod(root, 0o700)
            except OSError:
                pass
        return paths

    def _scan_environment(self) -> Dict[str, Any]:
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "cpu_count": _detect_cpu(),
            "memory_mb": _detect_memory_mb(),
            "disk_free_mb": _detect_disk_free_mb(self.root),
            "pid": os.getpid(),
            "user": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
        }

    def _derive_limits(self, env: Dict[str, Any], paths: BootPaths) -> Dict[str, Any]:
        cpu = int(env["cpu_count"])
        mem = int(env["memory_mb"])
        # Throttle parallel agent tasks to min(cpu*2, 15, mem/256).
        parallel = max(1, min(self.MAX_PARALLEL_TASKS, cpu * 2, mem // 256))
        return {
            "max_parallel_tasks": parallel,
            "loop_min_delay_s": 0.25 if cpu >= 4 else 0.75,
            "memory_soft_cap_mb": int(mem * 0.6),
            "memory_hard_cap_mb": int(mem * 0.85),
            "artifact_quota_mb": min(4096, env["disk_free_mb"] // 4),
        }

    def _write_manifest(self, ctx: BootContext) -> None:
        manifest = {
            "boot_id": ctx.boot_id,
            "started_at": ctx.started_at,
            "paths": ctx.paths.to_dict(),
            "env": ctx.env,
            "limits": ctx.limits,
        }
        tmp = ctx.manifest_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True))
        os.replace(tmp, ctx.manifest_path)


# ------------------------------ module run -------------------------------- #


def boot(root: Path | str | None = None) -> BootContext:
    """Top-level convenience: `from uac.bootstrap import boot`."""
    return Bootstrap(root).initialize()


if __name__ == "__main__":  # pragma: no cover
    ctx = boot()
    print(ctx.summary())
    print(json.dumps(ctx.limits, indent=2))
