"""
Social Media connector — Twitter/X platform API integration.

Uses platform (app-level) credentials from environment:
  TWITTER_API_KEY        — OAuth 1.0a Consumer Key
  TWITTER_API_SECRET     — OAuth 1.0a Consumer Secret
  TWITTER_BEARER_TOKEN   — App-only Bearer Token (read-only searches)
  TWITTER_ACCESS_TOKEN   — OAuth 1.0a Access Token (user-level write)
  TWITTER_REFRESH_TOKEN  — OAuth 2.0 Refresh Token

Capabilities:
  post_tweet(text)           — Post a tweet (OAuth 1.0a user auth)
  search_tweets(query, n)    — Search recent tweets (Bearer Token)
  get_user_tweets(username)  — Get a user's recent tweets
  get_trending(woeid)        — Get trending topics
  status()                   — Check API connectivity and rate limits
"""
from __future__ import annotations

import os
import json
import time
from typing import Any

# ── Credential loading ────────────────────────────────────────────────────────

def _env(key: str) -> str:
    try:
        from backend.app.core.config import env as cfg_env
        return cfg_env(key) or os.environ.get(key, "")
    except Exception:
        return os.environ.get(key, "")


def _get_creds() -> dict:
    return {
        "api_key": _env("TWITTER_API_KEY"),
        "api_secret": _env("TWITTER_API_SECRET"),
        "bearer_token": _env("TWITTER_BEARER_TOKEN"),
        "access_token": _env("TWITTER_ACCESS_TOKEN"),
        "access_secret": _env("TWITTER_ACCESS_SECRET"),
    }


# ── Twitter API v2 helpers ────────────────────────────────────────────────────

_BASE = "https://api.twitter.com/2"
_BASE_V1 = "https://api.twitter.com/1.1"


def _bearer_headers(bearer: str) -> dict:
    return {"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"}


def _oauth1_client(api_key: str, api_secret: str, access_token: str, access_secret: str):
    """Build a requests.Session with OAuth 1.0a signing."""
    try:
        from requests_oauthlib import OAuth1Session
        return OAuth1Session(
            client_key=api_key,
            client_secret=api_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_secret,
        )
    except ImportError:
        # Fall back to tweepy if requests_oauthlib not installed
        try:
            import tweepy
            auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
            return tweepy.API(auth)
        except ImportError:
            return None


# ── Public API ────────────────────────────────────────────────────────────────

def post_tweet(text: str, reply_to_id: str | None = None) -> dict:
    """Post a tweet using OAuth 1.0a user credentials."""
    creds = _get_creds()
    api_key = creds["api_key"]
    api_secret = creds["api_secret"]
    access_token = creds["access_token"]
    access_secret = creds["access_secret"]

    if not all([api_key, api_secret, access_token, access_secret]):
        return {"ok": False, "error": "Twitter OAuth credentials not configured (need TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)"}

    payload: dict = {"text": text[:280]}
    if reply_to_id:
        payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}

    try:
        from requests_oauthlib import OAuth1Session
        session = OAuth1Session(
            client_key=api_key,
            client_secret=api_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_secret,
        )
        resp = session.post(f"{_BASE}/tweets", json=payload, timeout=15)
        if resp.status_code in (200, 201):
            data = resp.json()
            tweet_id = data.get("data", {}).get("id", "")
            return {"ok": True, "tweet_id": tweet_id, "text": text, "url": f"https://x.com/i/web/status/{tweet_id}"}
        return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
    except ImportError:
        return {"ok": False, "error": "requests_oauthlib not installed. Run: pip install requests-oauthlib"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def search_tweets(query: str, max_results: int = 10) -> dict:
    """Search recent tweets using Bearer Token (app-only auth)."""
    creds = _get_creds()
    bearer = creds["bearer_token"]
    if not bearer:
        return {"ok": False, "error": "TWITTER_BEARER_TOKEN not configured"}

    try:
        import requests
        params = {
            "query": query,
            "max_results": min(max(max_results, 10), 100),
            "tweet.fields": "created_at,author_id,public_metrics,text",
            "expansions": "author_id",
            "user.fields": "username,name",
        }
        resp = requests.get(
            f"{_BASE}/tweets/search/recent",
            headers=_bearer_headers(bearer),
            params=params,
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            results = []
            for t in tweets:
                author = users.get(t.get("author_id", ""), {})
                results.append({
                    "id": t["id"],
                    "text": t["text"],
                    "author": author.get("username", "unknown"),
                    "name": author.get("name", ""),
                    "created_at": t.get("created_at", ""),
                    "metrics": t.get("public_metrics", {}),
                })
            return {"ok": True, "query": query, "count": len(results), "tweets": results}
        return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_user_tweets(username: str, max_results: int = 10) -> dict:
    """Get recent tweets from a specific user."""
    creds = _get_creds()
    bearer = creds["bearer_token"]
    if not bearer:
        return {"ok": False, "error": "TWITTER_BEARER_TOKEN not configured"}

    try:
        import requests
        # First get user ID
        user_resp = requests.get(
            f"{_BASE}/users/by/username/{username}",
            headers=_bearer_headers(bearer),
            timeout=10,
        )
        if user_resp.status_code != 200:
            return {"ok": False, "error": f"User not found: {username}"}
        user_id = user_resp.json().get("data", {}).get("id", "")
        if not user_id:
            return {"ok": False, "error": f"Could not resolve user ID for @{username}"}

        # Then get their tweets
        tweets_resp = requests.get(
            f"{_BASE}/users/{user_id}/tweets",
            headers=_bearer_headers(bearer),
            params={"max_results": min(max_results, 100), "tweet.fields": "created_at,public_metrics"},
            timeout=15,
        )
        if tweets_resp.status_code == 200:
            data = tweets_resp.json()
            return {"ok": True, "username": username, "tweets": data.get("data", [])}
        return {"ok": False, "error": f"HTTP {tweets_resp.status_code}: {tweets_resp.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_trending(woeid: int = 1) -> dict:
    """Get trending topics (WOEID 1 = worldwide). Uses v1.1 API (requires user auth)."""
    creds = _get_creds()
    if not all([creds["api_key"], creds["api_secret"], creds["access_token"], creds["access_secret"]]):
        return {"ok": False, "error": "OAuth credentials required for trending topics"}

    try:
        from requests_oauthlib import OAuth1Session
        session = OAuth1Session(
            client_key=creds["api_key"],
            client_secret=creds["api_secret"],
            resource_owner_key=creds["access_token"],
            resource_owner_secret=creds["access_secret"],
        )
        resp = session.get(f"{_BASE_V1}/trends/place.json", params={"id": woeid}, timeout=10)
        if resp.status_code == 200:
            trends = resp.json()[0].get("trends", [])[:20]
            return {"ok": True, "woeid": woeid, "trends": [{"name": t["name"], "tweet_volume": t.get("tweet_volume")} for t in trends]}
        return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def status() -> dict:
    """Check Twitter API connectivity."""
    creds = _get_creds()
    result = {
        "bearer_token_set": bool(creds["bearer_token"]),
        "oauth_credentials_set": bool(creds["api_key"] and creds["api_secret"]),
        "user_auth_set": bool(creds["access_token"]),
        "capabilities": [],
    }

    if result["bearer_token_set"]:
        result["capabilities"].extend(["search_tweets", "get_user_tweets"])
    if result["user_auth_set"]:
        result["capabilities"].extend(["post_tweet", "get_trending"])

    # Quick connectivity test
    if creds["bearer_token"]:
        try:
            import requests
            resp = requests.get(
                f"{_BASE}/tweets/search/recent",
                headers=_bearer_headers(creds["bearer_token"]),
                params={"query": "test", "max_results": 10},
                timeout=8,
            )
            result["api_reachable"] = resp.status_code in (200, 429)
            result["rate_limited"] = resp.status_code == 429
        except Exception as e:
            result["api_reachable"] = False
            result["connectivity_error"] = str(e)
    else:
        result["api_reachable"] = False

    return result
