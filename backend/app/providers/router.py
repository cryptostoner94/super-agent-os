"""
LLM Provider Router — local-first, cloud fallback.

Priority: Ollama (auto-detect) → Sandbox/Custom OpenAI → XAI → Gemini → Bedrock → OpenAI → Groq → OpenRouter

Supports OPENAI_BASE_URL for custom/proxy endpoints (e.g., Azure OpenAI, LiteLLM, Ollama OpenAI-compat, etc.)
"""
from __future__ import annotations
import json
import os
import requests
import requests.auth
from typing import Dict
from backend.app.core.config import env

class ProviderError(Exception):
    pass


class _BearerAuth(requests.auth.AuthBase):
    """Attach a Bearer token to outgoing requests using the standard auth interface."""
    def __init__(self, token: str) -> None:
        self._token = token

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        r.headers["Authorization"] = "Bearer " + self._token
        return r


def _extract_text(data: dict) -> str:
    if isinstance(data, dict):
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            msg = choices[0].get("message", {})
            if isinstance(msg, dict) and msg.get("content"):
                return str(msg["content"])
        for key in ("result", "text", "content", "response"):
            if key in data:
                return str(data[key])
    raise ProviderError("Could not parse LLM response")


def _ollama_smart(prompt: str) -> Dict[str, str]:
    """Auto-detect best available Ollama model via providers.ollama module."""
    from backend.app.providers.ollama import complete as ol_complete, is_available
    if not is_available():
        raise ProviderError("Ollama not reachable")
    result = ol_complete(prompt)
    prov = result.get("provider", "")
    if "error" in prov or "unavailable" in prov or "local_no_llm" in prov:
        raise ProviderError(result.get("text", "Ollama unavailable"))
    return result


def _openai_compat(prompt: str) -> Dict[str, str]:
    """
    OpenAI-compatible endpoint supporting custom base URLs.
    Reads OPENAI_BASE_URL (or OPENAI_API_BASE) for proxy/custom endpoints.
    Falls back to api.openai.com if not set.
    """
    key = env("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise ProviderError("OPENAI_API_KEY missing")

    # Support both OPENAI_BASE_URL and OPENAI_API_BASE (common aliases)
    base_url = (
        env("OPENAI_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL", "")
        or os.environ.get("OPENAI_API_BASE", "")
        or "https://api.openai.com/v1"
    ).rstrip("/")

    model = env("OPENAI_MODEL") or "gpt-4o-mini"
    url = f"{base_url}/chat/completions"

    r = requests.post(
        url,
        auth=_BearerAuth(key),
        headers={"Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.35},
        timeout=90,
    )
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    provider_label = "openai_proxy" if "openai.com" not in base_url else "openai"
    return {"provider": provider_label, "text": text, "model": model, "base_url": base_url}


def _xai(prompt: str) -> Dict[str, str]:
    key = env("XAI_API_KEY")
    model = env("XAI_MODEL", "grok-2-latest")
    if not key:
        raise ProviderError("XAI_API_KEY missing")
    r = requests.post(
        "https://api.x.ai/v1/chat/completions",
        auth=_BearerAuth(key),
        headers={"Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.35},
        timeout=90,
    )
    r.raise_for_status()
    return {"provider": "xai_grok", "text": r.json()["choices"][0]["message"]["content"]}


def _gemini(prompt: str) -> Dict[str, str]:
    key = env("GEMINI_API_KEY")
    model = env("GEMINI_MODEL", "gemini-1.5-flash")
    if not key:
        raise ProviderError("GEMINI_API_KEY missing")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    r = requests.post(
        url,
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=90,
    )
    r.raise_for_status()
    data = r.json()
    return {"provider": "gemini", "text": data["candidates"][0]["content"]["parts"][0]["text"]}


def _bedrock(prompt: str) -> Dict[str, str]:
    if not (env("AWS_ACCESS_KEY_ID") and env("AWS_SECRET_ACCESS_KEY")):
        raise ProviderError("AWS Bedrock credentials missing")
    import boto3
    client = boto3.client(
        "bedrock-runtime",
        region_name=env("AWS_REGION", "us-east-1"),
        aws_access_key_id=env("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=env("AWS_SECRET_ACCESS_KEY"),
    )
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1800,
        "messages": [{"role": "user", "content": prompt}],
    })
    model_id = env("BEDROCK_MODEL_ID", "anthropic.claude-3-5-haiku-20241022-v1:0")
    resp = client.invoke_model(modelId=model_id, body=body)
    data = json.loads(resp["body"].read())
    return {"provider": "bedrock", "text": data["content"][0]["text"]}


def _groq(prompt: str) -> Dict[str, str]:
    key = env("GROQ_API_KEY")
    if not key:
        raise ProviderError("GROQ_API_KEY missing")
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        auth=_BearerAuth(key),
        headers={"Content-Type": "application/json"},
        json={"model": env("GROQ_MODEL", "llama-3.3-70b-versatile"),
              "messages": [{"role": "user", "content": prompt}], "temperature": 0.35},
        timeout=90,
    )
    r.raise_for_status()
    return {"provider": "groq", "text": r.json()["choices"][0]["message"]["content"]}


def _openrouter(prompt: str) -> Dict[str, str]:
    key = env("OPENROUTER_API_KEY")
    if not key:
        raise ProviderError("OPENROUTER_API_KEY missing")
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        auth=_BearerAuth(key),
        headers={"Content-Type": "application/json"},
        json={"model": env("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
              "messages": [{"role": "user", "content": prompt}], "temperature": 0.35},
        timeout=90,
    )
    r.raise_for_status()
    return {"provider": "openrouter", "text": r.json()["choices"][0]["message"]["content"]}


# _openai_compat handles both standard OpenAI and custom base URLs
# It replaces the old _openai function and is tried before cloud-specific providers
_PROVIDERS = [_ollama_smart, _openai_compat, _xai, _gemini, _bedrock, _groq, _openrouter]


def complete(prompt: str) -> Dict[str, str]:
    """
    Local-first LLM router.
    1. Ollama (auto-detect installed models)
    2. OpenAI / OpenAI-compatible proxy (OPENAI_BASE_URL)
    3. XAI → Gemini → Bedrock → Groq → OpenRouter
    """
    errors: list[str] = []
    for fn in _PROVIDERS:
        try:
            return fn(prompt)
        except Exception as e:
            errors.append(f"{fn.__name__}: {e}")

    return {
        "provider": "local_no_llm",
        "text": (
            "No LLM available. To enable:\n"
            "  • Local: docker compose up ollama  (free, no API key)\n"
            "  • Cloud: set OPENAI_API_KEY (+ optionally OPENAI_BASE_URL), GROQ_API_KEY, or GEMINI_API_KEY in .env\n\n"
            "Errors: " + " | ".join(errors[-3:])
        ),
    }
