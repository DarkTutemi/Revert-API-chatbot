import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    PORT = int(os.getenv("PORT", "3000"))
    API_KEY = os.getenv("API_KEY", "change-me-to-a-long-random-string")
    CF_CHECK_INTERVAL = int(os.getenv("CF_CHECK_INTERVAL", "300"))
    CF_IMPERSONATE = os.getenv("CF_IMPERSONATE", "chrome124")
    ACCOUNTS_FILE = os.getenv("ACCOUNTS_FILE", "./accounts.txt")
    REFRESH_MARGIN_HOURS = float(os.getenv("REFRESH_MARGIN_HOURS", "1"))
    PROXY_URL = os.getenv("PROXY_URL", "http://localhost:3000")
    PROXY_API_KEY = os.getenv("PROXY_API_KEY", "change-me-to-a-long-random-string")

    CDP_PORT = int(os.getenv("CDP_PORT", "9222"))
    CDP_URL = f"http://localhost:{CDP_PORT}"

    UPSTREAM_BASE = "https://chatgpt.com"
    UPSTREAM_CONVERSATION = f"{UPSTREAM_BASE}/backend-api/f/conversation"
    UPSTREAM_SESSION = f"{UPSTREAM_BASE}/api/auth/session"

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    BASE_HEADERS = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": UPSTREAM_BASE,
        "Referer": f"{UPSTREAM_BASE}/",
        "Connection": "keep-alive",
    }
