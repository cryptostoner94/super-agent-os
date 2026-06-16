from __future__ import annotations

from collections import defaultdict
from typing import Dict, List
from .models_upgrade import MemorySignal


class LightweightMemory:
    def __init__(self) -> None:
        self._signals: Dict[str, List[MemorySignal]] = defaultdict(list)

    def add(self, namespace: str, signal: MemorySignal) -> None:
        self._signals[namespace].append(signal)

    def get(self, namespace: str) -> List[MemorySignal]:
        return list(self._signals.get(namespace, []))

    def summarize(self, namespace: str) -> dict:
        signals = self._signals.get(namespace, [])
        if not signals:
            return {"namespace": namespace, "count": 0, "highlights": []}
        top = sorted(signals, key=lambda x: x.weight, reverse=True)[:5]
        return {
            "namespace": namespace,
            "count": len(signals),
            "highlights": [
                {"key": s.key, "value": s.value, "weight": s.weight, "source": s.source}
                for s in top
            ],
        }
