from __future__ import annotations
import json
import requests
from typing import Dict
from backend.app.core.config import env, capabilities

class ProviderError(Exception):
    pass

def _xai(prompt: str) -> Dict[str, str]:
    key = env("XAI_API_KEY")
    model = env("XAI_MODEL", "grok-2-latest")
    if not key:
        raise ProviderError("XAI_API_KEY missing")
    r = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=90)
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
    resp = client.invoke_model(modelId=env("BEDROCK_MODEL_ID"), body=body)
    data = json.loads(resp["body"].read())
    return {"provider": "bedrock", "text": data["content"][0]["text"]}

def _openai(prompt: str) -> Dict[str, str]:
    key = env("OPENAI_API_KEY")
    if not key:
        raise ProviderError("OPENAI_API_KEY missing")
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": env("OPENAI_MODEL", "gpt-4o-mini"), "messages": [{"role": "user", "content": prompt}], "temperature": 0.35},
        timeout=90,
    )
    r.raise_for_status()
    return {"provider": "openai", "text": r.json()["choices"][0]["message"]["content"]}

def _groq(prompt: str) -> Dict[str, str]:
    key = env("GROQ_API_KEY")
    if not key:
        raise ProviderError("GROQ_API_KEY missing")
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": env("GROQ_MODEL", "llama-3.3-70b-versatile"), "messages": [{"role": "user", "content": prompt}], "temperature": 0.35},
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
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": env("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"), "messages": [{"role": "user", "content": prompt}], "temperature": 0.35},
        timeout=90,
    )
    r.raise_for_status()
    return {"provider": "openrouter", "text": r.json()["choices"][0]["message"]["content"]}

def complete(prompt: str) -> Dict[str, str]:
    """
    Main priority follows user preference:
    1. Grok/XAI
    2. Gemini
    3. Bedrock
    4. OpenAI
    Then uses extra configured providers as emergency fallback.
    """
    errors = []
    providers = [_xai, _gemini, _bedrock, _openai, _groq, _openrouter]
    for fn in providers:
        try:
            return fn(prompt)
        except Exception as e:
            errors.append(f"{fn.__name__}: {type(e).__name__}: {e}")
    return {
        "provider": "local_no_llm",
        "text": "No usable LLM provider responded. Configure XAI_API_KEY, GEMINI_API_KEY, AWS Bedrock, OPENAI_API_KEY, GROQ_API_KEY, or OPENROUTER_API_KEY in .env.\n\nErrors:\n" + "\n".join(errors[-5:]),
    }
