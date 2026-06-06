"""
SOUL
====
Core cognitive director.

Responsibilities
----------------
* Hold the motivation matrix (curiosity / safety / throughput / quality).
* Score every agent work-unit against a Zero-Error standard.
* Drive the autonomous loop: pick the next task, expose backpressure signals.

This module is deterministic and pure — all randomness uses `secrets` only.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# --------------------------- public dataclasses ---------------------------- #


@dataclass
class MotivationMatrix:
    """Weighted drives that bias scheduling and quality thresholds."""
    curiosity: float = 0.20   # explore new skills
    safety: float = 0.35      # refuse risky operations
    throughput: float = 0.20  # finish tasks quickly
    quality: float = 0.25     # zero-error standard

    def normalized(self) -> "MotivationMatrix":
        total = self.curiosity + self.safety + self.throughput + self.quality
        if total <= 0:
            return MotivationMatrix()
        return MotivationMatrix(
            curiosity=self.curiosity / total,
            safety=self.safety / total,
            throughput=self.throughput / total,
            quality=self.quality / total,
        )

    def as_dict(self) -> Dict[str, float]:
        return {
            "curiosity": self.curiosity,
            "safety": self.safety,
            "throughput": self.throughput,
            "quality": self.quality,
        }


@dataclass
class QualityVerdict:
    score: float            # 0.0 .. 1.0
    passed: bool
    reasons: List[str] = field(default_factory=list)
    retry_recommended: bool = False


# ------------------------------ Soul --------------------------------------- #


class Soul:
    """Cognitive director enforcing the zero-error standard."""

    ZERO_ERROR_THRESHOLD = 0.92  # score required to pass

    def __init__(
        self,
        motivation: Optional[MotivationMatrix] = None,
        memory_writer: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> None:
        self.motivation = (motivation or MotivationMatrix()).normalized()
        self._memory_writer = memory_writer
        self._cycle = 0
        self._last_scores: List[float] = []

    # ---------------------------- evaluation ------------------------------- #

    def evaluate(self, work_unit: Dict[str, Any]) -> QualityVerdict:
        """
        Score a finished work unit.

        Expected keys:
            status       : "ok" | "error" | "partial"
            errors       : list[str]
            warnings     : list[str]
            outputs      : dict (artifacts, returned values, ...)
            duration_ms  : float
            attempts     : int  (1-based)
        """
        status = work_unit.get("status", "error")
        errors = list(work_unit.get("errors") or [])
        warnings = list(work_unit.get("warnings") or [])
        outputs = work_unit.get("outputs") or {}
        duration = float(work_unit.get("duration_ms", 0.0))
        attempts = int(work_unit.get("attempts", 1))

        score = 1.0
        reasons: List[str] = []

        if status != "ok":
            score -= 0.55
            reasons.append(f"status={status}")
        if errors:
            score -= min(0.40, 0.10 * len(errors))
            reasons.append(f"{len(errors)} error(s)")
        if warnings:
            score -= min(0.15, 0.03 * len(warnings))
            reasons.append(f"{len(warnings)} warning(s)")
        if attempts > 1:
            score -= 0.05 * (attempts - 1)
            reasons.append(f"attempts={attempts}")
        if not outputs:
            score -= 0.10
            reasons.append("no outputs produced")
        # Throughput motivation gently rewards fast tasks (<2s).
        if duration and duration < 2000:
            score += 0.02 * self.motivation.throughput
        score = max(0.0, min(1.0, score))

        passed = (
            status == "ok"
            and not errors
            and score >= self.ZERO_ERROR_THRESHOLD
        )
        verdict = QualityVerdict(
            score=score,
            passed=passed,
            reasons=reasons,
            retry_recommended=(not passed) and attempts < 3 and status != "blocked",
        )

        self._last_scores.append(score)
        if len(self._last_scores) > 64:
            self._last_scores = self._last_scores[-64:]

        if self._memory_writer:
            try:
                self._memory_writer(
                    "soul_verdict",
                    {
                        "cycle": self._cycle,
                        "score": verdict.score,
                        "passed": verdict.passed,
                        "reasons": verdict.reasons,
                        "ts": time.time(),
                    },
                )
            except Exception:  # memory must never crash the soul
                pass

        return verdict

    # ----------------------------- scheduling ------------------------------ #

    def rank_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return tasks sorted by motivation-weighted urgency score (desc)."""
        m = self.motivation
        def urgency(t: Dict[str, Any]) -> float:
            risk = float(t.get("risk", 0.3))           # 0..1
            novelty = float(t.get("novelty", 0.5))     # 0..1
            cost = float(t.get("cost", 0.3))           # 0..1, latency proxy
            value = float(t.get("value", 0.5))         # 0..1
            return (
                m.curiosity * novelty
                + m.safety * (1.0 - risk)
                + m.throughput * (1.0 - cost)
                + m.quality * value
            )
        return sorted(tasks, key=urgency, reverse=True)

    # ------------------------------ stats --------------------------------- #

    def tick(self) -> int:
        self._cycle += 1
        return self._cycle

    def rolling_quality(self) -> float:
        if not self._last_scores:
            return 1.0
        return sum(self._last_scores) / len(self._last_scores)

    def health_signal(self) -> Dict[str, Any]:
        rq = self.rolling_quality()
        return {
            "cycle": self._cycle,
            "rolling_quality": rq,
            "motivation": self.motivation.as_dict(),
            "zero_error_ok": rq >= self.ZERO_ERROR_THRESHOLD,
            "fatigue": 1.0 - math.exp(-self._cycle / 1000.0),  # soft saturation
        }
