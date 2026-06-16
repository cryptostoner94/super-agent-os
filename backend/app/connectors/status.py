from backend.app.core.config import capabilities
from backend.app.connectors.registry import all_connectors


def connector_status() -> list[dict]:
    """Return integration connector status (backward-compatible list format)."""
    caps = capabilities()
    return [
        {"id": "telegram", "name": "Telegram", "category": "messaging", "enabled": caps["connectors"]["telegram"]},
        {"id": "github", "name": "GitHub", "category": "code", "enabled": caps["connectors"]["github"]},
        {"id": "supabase", "name": "Supabase", "category": "database", "enabled": caps["connectors"]["supabase"]},
        {"id": "google", "name": "Google/Gmail/Drive", "category": "productivity", "enabled": caps["connectors"]["google"]},
        {"id": "notion", "name": "Notion", "category": "productivity", "enabled": caps["connectors"]["notion"]},
        {"id": "airtable", "name": "Airtable", "category": "database", "enabled": caps["connectors"]["airtable"]},
        {"id": "slack", "name": "Slack", "category": "messaging", "enabled": caps["connectors"]["slack"]},
        {"id": "stripe", "name": "Stripe", "category": "payments", "enabled": caps["connectors"]["stripe"]},
    ]


def bounty_platform_status() -> list[dict]:
    """Return bounty platform connector status."""
    return all_connectors()
