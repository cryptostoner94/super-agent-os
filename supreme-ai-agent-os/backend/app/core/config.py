from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import os

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ENV_PATH)

def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()

def is_enabled(name: str) -> bool:
    return bool(env(name))

@dataclass(frozen=True)
class Settings:
    app_name: str = "Supreme AI Agent OS"
    workspace_dir: str = env("SUPREME_WORKSPACE_DIR", str(ROOT_DIR / "data"))
    allow_terminal: bool = env("SUPREME_ALLOW_TERMINAL", "true").lower() == "true"
    api_url: str = env("SUPREME_API_URL", "http://127.0.0.1:8000")
    public_url: str = env("SUPREME_PUBLIC_URL", "http://127.0.0.1:8501")

settings = Settings()
Path(settings.workspace_dir).mkdir(parents=True, exist_ok=True)
(Path(settings.workspace_dir) / "artifacts").mkdir(parents=True, exist_ok=True)

def capabilities() -> dict:
    return {
        "llm": {
            "xai_grok": is_enabled("XAI_API_KEY"),
            "gemini": is_enabled("GEMINI_API_KEY"),
            "bedrock": is_enabled("AWS_ACCESS_KEY_ID") and is_enabled("AWS_SECRET_ACCESS_KEY"),
            "openai": is_enabled("OPENAI_API_KEY"),
            "groq": is_enabled("GROQ_API_KEY"),
            "openrouter": is_enabled("OPENROUTER_API_KEY"),
            "together": is_enabled("TOGETHER_API_KEY"),
            "fireworks": is_enabled("FIREWORKS_API_KEY"),
        },
        "search": {
            "tavily": is_enabled("TAVILY_API_KEY"),
            "serper": is_enabled("SERPER_API_KEY"),
            "firecrawl": is_enabled("FIRECRAWL_API_KEY"),
            "brave": is_enabled("BRAVE_SEARCH_API_KEY"),
        },
        "browser": {
            "browserless": is_enabled("BROWSERLESS_API_KEY"),
            "playwright": env("PLAYWRIGHT_ENABLED", "false").lower() == "true",
            "skyvern": is_enabled("SKYVERN_API_KEY") or is_enabled("SKYVERN_API_URL"),
            "openclaw": is_enabled("OPENCLAW_API_URL"),
            "apify": is_enabled("APIFY_API_TOKEN"),
        },
        "connectors": {
            "github": is_enabled("GITHUB_TOKEN"),
            "gitlab": is_enabled("GITLAB_TOKEN"),
            "telegram": is_enabled("TELEGRAM_BOT_TOKEN"),
            "supabase": is_enabled("SUPABASE_URL") and is_enabled("SUPABASE_SERVICE_ROLE_KEY"),
            "google": is_enabled("GOOGLE_CLIENT_ID") and is_enabled("GOOGLE_REFRESH_TOKEN"),
            "notion": is_enabled("NOTION_API_KEY"),
            "airtable": is_enabled("AIRTABLE_API_KEY"),
            "slack": is_enabled("SLACK_CLIENT_ID") and is_enabled("SLACK_CLIENT_SECRET"),
            "stripe": is_enabled("STRIPE_SECRET_KEY"),
        },
        "finance": {
            "alpha_vantage": is_enabled("ALPHA_VANTAGE_API_KEY"),
            "polygon": is_enabled("POLYGON_API_KEY"),
            "finnhub": is_enabled("FINNHUB_API_KEY"),
            "coingecko": is_enabled("COINGECKO_API_KEY"),
        },
        "core": {
            "terminal": settings.allow_terminal,
            "artifacts": True,
            "library": True,
            "skills": True,
            "scheduler_registry": True,
        }
    }
