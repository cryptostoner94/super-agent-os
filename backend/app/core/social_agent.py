"""
Social agent — posts updates to X (@Aria_Loop) and sends Gmail notifications.
Primary: Twitter API v2 via tweepy. Fallback: browser automation (Playwright).
"""
from __future__ import annotations
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

AGENT_EMAIL = os.getenv("AGENT_EMAIL", "")
AGENT_EMAIL_PASSWORD = os.getenv("AGENT_EMAIL_PASSWORD", "")
SMTP_HOST = os.getenv("AGENT_EMAIL_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("AGENT_EMAIL_SMTP_PORT", "587"))

AGENT_X_USERNAME = os.getenv("AGENT_X_USERNAME", "")
AGENT_X_EMAIL = os.getenv("AGENT_X_EMAIL", "")
AGENT_X_PASSWORD = os.getenv("AGENT_X_PASSWORD", "")

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")


def send_agent_email(subject: str, body: str, to: str | None = None) -> dict:
    """Send email via Gmail SMTP (STARTTLS)."""
    if not AGENT_EMAIL or not AGENT_EMAIL_PASSWORD:
        return {"ok": False, "error": "AGENT_EMAIL credentials not set"}
    recipient = to or AGENT_EMAIL
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Super Agent OS <{AGENT_EMAIL}>"
        msg["To"] = recipient
        msg.attach(MIMEText(body, "plain"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.login(AGENT_EMAIL, AGENT_EMAIL_PASSWORD)
            server.sendmail(AGENT_EMAIL, recipient, msg.as_string())
        return {"ok": True, "to": recipient, "subject": subject}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _post_via_tweepy(text: str) -> dict:
    """Post tweet using Twitter API v2 (tweepy). Requires OAuth 1.0a credentials."""
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        return {"ok": False, "error": "Twitter OAuth 1.0a credentials incomplete"}
    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
        )
        response = client.create_tweet(text=text)
        tweet_id = response.data.get("id") if response.data else None
        return {"ok": True, "tweet_id": tweet_id, "method": "api_v2"}
    except Exception as e:
        return {"ok": False, "error": str(e), "method": "api_v2"}


async def _post_via_browser(text: str) -> dict:
    """Post tweet via browser automation (Playwright). Used when API keys unavailable."""
    if not AGENT_X_EMAIL or not AGENT_X_PASSWORD:
        return {"ok": False, "error": "X browser credentials not set"}
    if len(text) > 280:
        text = text[:277] + "..."
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                executable_path=os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "/usr/bin/chromium"),
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            )
            ctx = await browser.new_context()
            page = await ctx.new_page()

            await page.goto("https://x.com/login", timeout=30000)
            await page.wait_for_selector('input[autocomplete="username"]', timeout=15000)
            await page.fill('input[autocomplete="username"]', AGENT_X_EMAIL)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(1500)

            try:
                usr_field = await page.wait_for_selector('input[data-testid="ocfEnterTextTextInput"]', timeout=4000)
                await usr_field.fill(AGENT_X_USERNAME)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(1000)
            except Exception:
                pass

            await page.wait_for_selector('input[name="password"]', timeout=10000)
            await page.fill('input[name="password"]', AGENT_X_PASSWORD)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)

            await page.goto("https://x.com/compose/tweet", timeout=20000)
            await page.wait_for_selector('[data-testid="tweetTextarea_0"]', timeout=10000)
            await page.fill('[data-testid="tweetTextarea_0"]', text)
            await page.wait_for_timeout(800)
            await page.click('[data-testid="tweetButtonInline"]')
            await page.wait_for_timeout(2000)
            await browser.close()
        return {"ok": True, "posted": text[:60] + "...", "method": "browser"}
    except Exception as e:
        return {"ok": False, "error": str(e), "method": "browser"}


async def post_to_x(text: str) -> dict:
    """Post to X (@Aria_Loop). Tries API v2 first, falls back to browser automation."""
    if len(text) > 280:
        text = text[:277] + "..."

    # Prefer API v2 (faster, more reliable, no browser needed)
    if TWITTER_API_KEY and TWITTER_API_SECRET and TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_TOKEN_SECRET:
        result = _post_via_tweepy(text)
        if result["ok"]:
            return result

    # Fall back to browser automation
    return await _post_via_browser(text)


def build_earnings_tweet(summary: dict) -> str:
    """Build a concise tweet summarising agent activity."""
    submitted = summary.get("submitted", 0)
    queued = summary.get("queued", 0)
    platforms = summary.get("platforms", [])
    platform_str = "/".join(p.capitalize() for p in platforms[:3])
    if submitted > 0:
        return (
            f"🤖 Agent update: {submitted} vulnerability report(s) submitted to {platform_str}. "
            f"Pipeline running 24/7. #BugBounty #AI #SuperAgentOS"
        )
    elif queued > 0:
        return f"🔍 Agent pipeline active: {queued} finding(s) queued for review on {platform_str}. #BugBounty #AI"
    else:
        return f"🧠 Super Agent OS scanning {platform_str} bounty programs. 24/7 autonomous security research. #BugBounty #AI"
