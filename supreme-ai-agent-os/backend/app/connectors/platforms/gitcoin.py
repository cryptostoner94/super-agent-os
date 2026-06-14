"""
Gitcoin Connector
=================
Mode: api (GraphQL + REST)
Auth: API key for posting; public GraphQL for reading

Gitcoin exposes a public GraphQL API at gitcoin.co/api/v0.1 and a
legacy REST API. Reading bounties is unauthenticated. Creating or
claiming bounties requires wallet-based auth (Web3/Gitcoin Passport).

Payout is in ETH/ERC20 tokens — blockchain verification required.
"""
from __future__ import annotations
import os

CONNECTOR_META = {
    "name": "Gitcoin",
    "url": "https://gitcoin.co",
    "mode": "api",
    "auth_mode": "web3_wallet_for_claiming",
    "auth_env": ["GITCOIN_API_KEY"],
    "ingest_status": "api_ready",
    "submission_status": "wallet_required",
    "payout_tracking": "blockchain_only",
    "notes": "Public bounty listing via REST API. Claiming/submission requires Web3 wallet. Payouts on-chain.",
}

API_BASE = "https://gitcoin.co/api/v0.1"


async def fetch_bounties(limit: int = 25, network: str = "mainnet") -> dict:
    """Fetch open bounties from Gitcoin public API."""
    import httpx
    try:
        params = {"network": network, "is_open": "true", "limit": limit}
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{API_BASE}/bounties/", params=params)
            r.raise_for_status()
            data = r.json()
            normalized = []
            for b in (data if isinstance(data, list) else data.get("results", [])):
                normalized.append({
                    "id": b.get("pk", b.get("id")),
                    "title": b.get("title", ""),
                    "description": b.get("issue_description_text", "")[:300],
                    "value": b.get("value_in_usdt_now"),
                    "token": b.get("token_name"),
                    "url": b.get("url", ""),
                    "status": b.get("status", "open"),
                    "keywords": b.get("keywords", ""),
                })
            return {"ok": True, "source": "gitcoin", "count": len(normalized), "data": normalized}
    except Exception as e:
        return {"ok": False, "error": str(e), "data": []}


async def get_status() -> dict:
    api_key = bool(os.getenv("GITCOIN_API_KEY", ""))
    return {
        "connector": "gitcoin",
        "mode": "api",
        "credentials_present": api_key,
        "ready": True,
        "note": "Bounty listing requires no auth. Submission requires Web3 wallet. Set GITCOIN_API_KEY for extended access.",
    }
