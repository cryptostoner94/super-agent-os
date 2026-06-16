"""
HEARTBEAT
=========
Async cron / pulse orchestrator.

Responsibilities
----------------
* Track system health (uptime, loop latency, gc, memory pressure).
* Throttle the executor based on Bootstrap-derived limits.
* Run periodic pulses (cron-like, async) for memory cleanup, manifest refresh,
  and self-diagnostics.
"""
from __future__ import annotations

import asyncio
import gc
import os
import resource
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional


@dataclass
class PulseStats:
    started_at: float = field(default_factory=time.time)
    pulses: int = 0
    last_latency_ms: float = 0.0
    last_gc_collected: int = 0
    last_rss_mb: float = 0.0
    throttled: bool = False
    errors: int = 0

    def uptime_s(self) -> float:
        return time.time() - self.started_at

    def snapshot(self) -> Dict[str, Any]:
        return {
            "uptime_s": self.uptime_s(),
            "pulses": self.pulses,
            "last_latency_ms": self.last_latency_ms,
            "last_gc_collected": self.last_gc_collected,
            "last_rss_mb": self.last_rss_mb,
            "throttled": self.throttled,
            "errors": self.errors,
        }


def _rss_mb() -> float:
    """Resident set size in MB (POSIX best-effort)."""
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Linux returns kB, macOS returns bytes.
        if os.uname().sysname == "Darwin":
            return usage / (1024 * 1024)
        return usage / 1024
    except Exception:
        return 0.0


class Heartbeat:
    """Drives periodic async tasks and enforces resource throttling."""

    def __init__(
        self,
        limits: Dict[str, Any],
        period_s: float = 2.0,
    ) -> None:
        self.limits = limits
        self.period_s = max(0.25, float(period_s))
        self.stats = PulseStats()
        self._tasks: List[Callable[[], Awaitable[None]]] = []
        self._stop = asyncio.Event()
        self._loop_lock = asyncio.Lock()

    # -------------------------- task registry ----------------------------- #

    def register(self, coro_factory: Callable[[], Awaitable[None]]) -> None:
        """Register an awaitable factory called on every pulse."""
        self._tasks.append(coro_factory)

    # --------------------------- lifecycle -------------------------------- #

    async def run_forever(self, max_pulses: Optional[int] = None) -> None:
        """
        Pulse loop. `max_pulses` is provided so tests / demos can terminate.
        """
        while not self._stop.is_set():
            t0 = time.perf_counter()
            try:
                await self._single_pulse()
            except Exception:  # never crash the heartbeat itself
                self.stats.errors += 1
            elapsed = (time.perf_counter() - t0) * 1000.0
            self.stats.last_latency_ms = elapsed
            self.stats.pulses += 1
            if max_pulses is not None and self.stats.pulses >= max_pulses:
                break
            # Adaptive sleep: lengthen interval when under memory pressure.
            sleep_s = self.period_s
            if self.stats.throttled:
                sleep_s *= 2.0
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=sleep_s)
            except asyncio.TimeoutError:
                pass

    def stop(self) -> None:
        self._stop.set()

    # ---------------------------- internals ------------------------------- #

    async def _single_pulse(self) -> None:
        async with self._loop_lock:
            # 1. Resource snapshot.
            rss = _rss_mb()
            self.stats.last_rss_mb = rss
            soft = float(self.limits.get("memory_soft_cap_mb", 1e12))
            hard = float(self.limits.get("memory_hard_cap_mb", 1e12))
            if rss >= hard:
                self.stats.throttled = True
                gc_collected = gc.collect()
                self.stats.last_gc_collected = gc_collected
            elif rss >= soft:
                self.stats.throttled = True
            else:
                self.stats.throttled = False

            # 2. Run registered tasks with bounded concurrency.
            if self._tasks:
                # Each pulse runs ALL registered tasks concurrently but bounded.
                sem = asyncio.Semaphore(int(self.limits.get("max_parallel_tasks", 4)))

                async def _runner(factory: Callable[[], Awaitable[None]]) -> None:
                    async with sem:
                        try:
                            await factory()
                        except Exception:
                            self.stats.errors += 1

                await asyncio.gather(*(_runner(f) for f in self._tasks))
