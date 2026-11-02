"""
Entry point: CF bypass → load account pool → serve.
"""
import os
import logging
import uuid

from dotenv import load_dotenv

load_dotenv()

from config import Config
from auth.login import login_and_get_cookie

log = logging.getLogger("main")


def load_accounts(path: str) -> list[tuple[str, str]]:
    """accounts.txt — one EMAIL:PASSWORD per line. '#' = comment."""
    if not os.path.exists(path):
        return []
    accounts = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line and not line.startswith("eyJh"):
                email, password = line.split(":", 1)
                accounts.append(("userpass", email, password))
            else:
                accounts.append(("token", line, ""))
    return accounts


def main():
    from api.app import app, cf_manager, token_pool
    import uvicorn

    # 1. CF clearance
    log.info("Acquiring Cloudflare clearance...")
    if not cf_manager.acquire():
        log.error("FATAL: CF bypass failed on startup. Retry or check network.")
        raise SystemExit(1)

    # 2. Account pool via Playwright login
    accounts = load_accounts(Config.ACCOUNTS_FILE)
    log.info("Loading %d account(s)...", len(accounts))
    for item in accounts:
        mode = item[0]
        if mode == "token":
            account_id = f"acct_{uuid.uuid4().hex[:8]}"
            try:
                token_pool.add_account(account_id, item[1])
            except Exception as e:
                log.error("Failed to add token account: %s", e)
        else:
            email, password = item[1], item[2]
            cookie = login_and_get_cookie(email, password)
            if cookie:
                account_id = f"acct_{email.split('@')[0]}"
                try:
                    token_pool.add_account(account_id, cookie)
                except Exception as e:
                    log.error("Failed to add %s: %s", email, e)
            else:
                log.warning("Login failed for %s — skipped", email)

    # 3. Serve
    if not token_pool.accounts:
        log.warning(
            "No accounts loaded. Server starts empty — "
            "POST /admin/add-account with a session cookie to add one."
        )

    log.info("Serving on :%d", Config.PORT)
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)


if __name__ == "__main__":
    main()
