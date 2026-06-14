# Platform Connectors

All 6 bounty/task platform connectors are present as real modules under `backend/app/connectors/platforms/`.

## Connector Status Table

| Platform | Module | Mode | Auth Required | Ingest | Submission | Payout Tracking |
|---|---|---|---|---|---|---|
| **Bugcrowd** | ✅ present | browser_automation | BUGCROWD_EMAIL + BUGCROWD_PASSWORD | browser_automation_ready | browser_automation_ready | dashboard_scrape |
| **Intigriti** | ✅ present | api | INTIGRITI_TOKEN | api_ready | api_ready | api_ready |
| **YesWeHack** | ✅ present | api | YESWEHACK_EMAIL + YESWEHACK_PASSWORD | api_ready | api_ready | api_partial |
| **Open Bug Bounty** | ✅ present | browser_automation | None (public read) | public_scrape_ready | manual_session_required | unavailable |
| **Gitcoin** | ✅ present | api | None (read) / Web3 wallet (submit) | api_ready | wallet_required | blockchain_only |
| **Huntr** | ✅ present | api | HUNTR_API_KEY | api_partial | browser_automation_fallback | manual |

## API Truth

| Platform | Public API? | Notes |
|---|---|---|
| Bugcrowd | ❌ No stable public researcher API | Internal API used after browser session |
| Intigriti | ✅ Yes | `api.intigriti.com/core/researcher` — needs OAuth token |
| YesWeHack | ✅ Yes | `api.yeswehack.com` — JWT auth |
| Open Bug Bounty | ❌ No | Public HTML only, scraped via httpx/BeautifulSoup |
| Gitcoin | ✅ Yes (read) | `gitcoin.co/api/v0.1/bounties` — unauthenticated read |
| Huntr | ⚠️ Limited | API exists but partial; browser fallback for submissions |

## Adding Credentials

Set the following env vars in `.env` (or Railway/Render dashboard):

```bash
# Bugcrowd
BUGCROWD_EMAIL=your@email.com
BUGCROWD_PASSWORD=yourpassword

# Intigriti (preferred — clean API)
INTIGRITI_TOKEN=your_personal_access_token

# YesWeHack
YESWEHACK_EMAIL=your@email.com
YESWEHACK_PASSWORD=yourpassword

# Gitcoin (optional — public read works without key)
GITCOIN_API_KEY=your_api_key

# Huntr
HUNTR_API_KEY=your_api_key
```

## Enabling a Connector

All connectors are always present. They enable/disable based on credentials.
Call `GET /bounty-platforms` to see live status.
Call `GET /api/connectors/all` for full integration + platform status.
