from __future__ import annotations

from typing import List
from backend.app.core.models_upgrade import ConnectorStatus, Opportunity


class BaseConnector:
    name: str = "base"

    def status(self) -> ConnectorStatus:
        raise NotImplementedError

    def ingest(self) -> List[Opportunity]:
        return []
