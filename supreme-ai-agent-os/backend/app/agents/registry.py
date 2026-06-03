AGENTS = [
    {
        "id": "executive",
        "name": "Executive Agent",
        "role": "Plans, decomposes, delegates, and verifies complex tasks.",
        "visible": True,
    },
    {
        "id": "builder",
        "name": "Builder Agent",
        "role": "Creates code, repo structures, deployment scripts, and artifacts.",
        "visible": True,
    },
    {
        "id": "terminal",
        "name": "Terminal Execution Agent",
        "role": "Executes approved backend commands and returns logs/results.",
        "visible": True,
    },
    {
        "id": "researcher",
        "name": "Research Agent",
        "role": "Performs research when search connectors are configured.",
        "requires_any": ["tavily", "serper", "firecrawl", "brave"],
    },
    {
        "id": "browser",
        "name": "Browser Operator",
        "role": "Automates browser actions when Browserless/Playwright/Skyvern/OpenClaw is configured.",
        "requires_any": ["browserless", "playwright", "skyvern", "openclaw"],
    },
    {
        "id": "finance",
        "name": "Finance and Opportunity Agent",
        "role": "Tracks markets and money workflows when finance data connectors are configured.",
        "requires_any": ["alpha_vantage", "polygon", "finnhub", "coingecko"],
    },
]
