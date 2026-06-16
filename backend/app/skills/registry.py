SKILLS = [
    {"id": "repo_builder", "name": "Repo Builder", "desc": "Create GitHub-ready repo structures and code scaffolds.", "requires": []},
    {"id": "terminal_exec", "name": "Terminal Executor", "desc": "Run approved terminal commands on the backend.", "requires": []},
    {"id": "data_lab", "name": "Data Lab", "desc": "Parse logs, JSON, CSV, ENV files, and notes.", "requires": []},
    {"id": "artifact_factory", "name": "Artifact Factory", "desc": "Create HTML, Markdown, CSV, XLSX and document-style outputs.", "requires": []},
    {"id": "browser_operator", "name": "Browser Operator", "desc": "Use Browserless/Playwright/Skyvern/OpenClaw when configured.", "requires_any": ["browserless", "playwright", "skyvern", "openclaw"]},
    {"id": "research_engine", "name": "Research Engine", "desc": "Use Tavily, Serper, Firecrawl, or Brave Search when configured.", "requires_any": ["tavily", "serper", "firecrawl", "brave"]},
    {"id": "github_operator", "name": "GitHub Operator", "desc": "Use GitHub API when GITHUB_TOKEN exists.", "requires": ["github"]},
    {"id": "telegram_operator", "name": "Telegram Operator", "desc": "Enable Telegram control when bot token exists.", "requires": ["telegram"]},
    {"id": "finance_tools", "name": "Finance Tools", "desc": "Market/crypto data tools when finance APIs exist.", "requires_any": ["alpha_vantage", "polygon", "finnhub", "coingecko"]},
]
