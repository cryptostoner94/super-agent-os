from backend.app.core.config import capabilities

def connector_status() -> list[dict]:
    caps = capabilities()
    return [
        {"id": "telegram", "name": "Telegram", "enabled": caps["connectors"]["telegram"]},
        {"id": "github", "name": "GitHub", "enabled": caps["connectors"]["github"]},
        {"id": "supabase", "name": "Supabase", "enabled": caps["connectors"]["supabase"]},
        {"id": "google", "name": "Google/Gmail/Drive/Calendar", "enabled": caps["connectors"]["google"]},
        {"id": "notion", "name": "Notion", "enabled": caps["connectors"]["notion"]},
        {"id": "airtable", "name": "Airtable", "enabled": caps["connectors"]["airtable"]},
        {"id": "slack", "name": "Slack", "enabled": caps["connectors"]["slack"]},
        {"id": "stripe", "name": "Stripe", "enabled": caps["connectors"]["stripe"]},
    ]
