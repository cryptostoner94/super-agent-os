from __future__ import annotations

from typing import Dict, List
from backend.app.core.models_upgrade import ConnectorMode, ConnectorStatus, Opportunity
from .base import BaseConnector


class BugcrowdConnector(BaseConnector):
    name = "Bugcrowd"
    def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            platform=self.name,
            mode=ConnectorMode.BROWSER_AUTOMATION,
            auth_requirement="researcher account; some programs require identity verification",
            ingest_ready=True,
            submission_ready=False,
            payout_tracking_ready=False,
            notes="Use browser automation/manual session; avoid fabricated researcher API.",
        )


class IntigritiConnector(BaseConnector):
    name = "Intigriti"
    def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            platform=self.name,
            mode=ConnectorMode.API,
            auth_requirement="account + token/session",
            ingest_ready=True,
            submission_ready=False,
            payout_tracking_ready=True,
            notes="API/token-assisted ingestion can be layered in if credentials exist.",
        )


class YesWeHackConnector(BaseConnector):
    name = "YesWeHack"
    def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            platform=self.name,
            mode=ConnectorMode.API,
            auth_requirement="account + token/session",
            ingest_ready=True,
            submission_ready=False,
            payout_tracking_ready=True,
            notes="Keep honest about researcher-vs-owner API limitations.",
        )


class OpenBugBountyConnector(BaseConnector):
    name = "Open Bug Bounty"
    def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            platform=self.name,
            mode=ConnectorMode.MANUAL_SESSION_REQUIRED,
            auth_requirement="site account; no practical public researcher API",
            ingest_ready=False,
            submission_ready=False,
            payout_tracking_ready=False,
            notes="Treat as manual or browser-assisted only.",
        )


class GitcoinConnector(BaseConnector):
    name = "Gitcoin"
    def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            platform=self.name,
            mode=ConnectorMode.MANUAL_SESSION_REQUIRED,
            auth_requirement="wallet connection + browser session",
            ingest_ready=True,
            submission_ready=False,
            payout_tracking_ready=True,
            notes="Wallet/browser interaction required; do not invent API.",
        )


class HuntrConnector(BaseConnector):
    name = "Huntr"
    def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            platform=self.name,
            mode=ConnectorMode.BROWSER_AUTOMATION,
            auth_requirement="site account/session",
            ingest_ready=True,
            submission_ready=False,
            payout_tracking_ready=False,
            notes="Use browser automation/manual session only.",
        )


def get_connectors() -> List[BaseConnector]:
    return [
        BugcrowdConnector(),
        IntigritiConnector(),
        YesWeHackConnector(),
        OpenBugBountyConnector(),
        GitcoinConnector(),
        HuntrConnector(),
    ]


def get_connector_statuses() -> List[ConnectorStatus]:
    return [connector.status() for connector in get_connectors()]
