"""
Ollama local LLM provider — auto-detects models, no API key required.
Supported: qwen2.5, qwen2.5-coder, llama3.2, mistral (and any other installed model).
"""
from __future__ import annotations
import os, requests
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
PREFERRED = ["qwen2.5", "llama3.2", "qwen2.5-coder", "mistral", "llama3.1", "llama3", "gemma2", "phi3"]

_detected: list[str] | None = None


def list_models() -> list[str]:
    global _detected
    if _detected is not None:
        return _detected
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        r.raise_for_status()
        _detected = [m["name"] for m in r.json().get("models", [])]
        return _detected
    except Exception:
        _detected = []
        return []


def best_model(prefer_code: bool = False) -> str | None:
    avail = list_models()
    if not avail:
        return None
    preferred = (["qwen2.5-coder"] + PREFERRED) if prefer_code else PREFERRED
    for p in preferred:
        for a in avail:
            if p in a:
                return a
    return avail[0]


def get_llm(model: str | None = None, temperature: float = 0.2):
    """Return LangChain ChatOllama instance or None if unavailable."""
    m = model or best_model()
    if not m:
        return None
    return ChatOllama(model=m, base_url=OLLAMA_BASE, temperature=temperature)


def complete(prompt: str, model: str | None = None, system: str | None = None) -> dict:
    m = model or best_model()
    if not m:
        return {"provider": "ollama_unavailable",
                "text": "Ollama not running or no models installed. "
                        "Run: ollama pull qwen2.5"}
    try:
        llm = ChatOllama(model=m, base_url=OLLAMA_BASE, temperature=0.2)
        msgs = []
        if system:
            msgs.append(SystemMessage(content=system))
        msgs.append(HumanMessage(content=prompt))
        resp = llm.invoke(msgs)
        return {"provider": f"ollama/{m}", "text": resp.content}
    except Exception as e:
        return {"provider": "ollama_error", "text": f"Ollama error ({m}): {e}"}


def is_available() -> bool:
    return bool(list_models())


def status() -> dict:
    models = list_models()
    return {
        "available": bool(models),
        "base_url": OLLAMA_BASE,
        "models": models,
        "best": best_model(),
        "best_coder": best_model(prefer_code=True),
    }
