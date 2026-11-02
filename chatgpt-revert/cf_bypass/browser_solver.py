"""
Playwright-based CF challenge solver (Turnstile escalation path).

Spawns a real Chromium, navigates to the target, waits for the
challenge to auto-resolve, extracts cf_clearance + UA, closes.
"""
import asyncio
import logging

log = logging.getLogger("cf_bypass.browser")

STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
window.chrome = { runtime: {} };
"""


async def _solve(url: str) -> dict | None:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # headed mode is far less detectable
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1920,1080",
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        await context.add_init_script(STEALTH_INIT_SCRIPT)

        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded")

        # Poll up to 30s for cf_clearance to appear
        for _ in range(30):
            cookies = await context.cookies()
            clearance = next(
                (c for c in cookies if c["name"] == "cf_clearance"), None
            )
            if clearance:
                ua = await page.evaluate("navigator.userAgent")
                await browser.close()
                return {"cf_clearance": clearance["value"], "user_agent": ua}
            await asyncio.sleep(1)

        await browser.close()
        return None


def solve_challenge_via_browser(url: str) -> dict | None:
    """Sync entry point used by CFSessionManager."""
    try:
        return asyncio.run(_solve(url))
    except Exception as e:
        log.error("Browser solver crashed: %s", e)
        return None
