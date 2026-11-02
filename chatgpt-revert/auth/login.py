"""
Playwright-based ChatGPT login → __Secure-next-auth.session-token.
Used on cold start or when a session cookie dies (~30 days).
"""
import asyncio
import logging

log = logging.getLogger("auth.login")


async def _login(email: str, password: str) -> str | None:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto("https://chatgpt.com/auth/login", wait_until="domcontentloaded")

            await page.wait_for_selector("button[data-testid='login-button']", timeout=15000)
            await page.click("button[data-testid='login-button']")

            await page.wait_for_selector("input[name='email']", timeout=15000)
            await page.fill("input[name='email']", email)
            await page.click("button[type='submit']")

            await page.wait_for_selector("input[name='password']", timeout=15000)
            await page.fill("input[name='password']", password)
            await page.click("button[type='submit']")

            await page.wait_for_url("**chatgpt.com/**", timeout=60000)

            cookies = await context.cookies()
            session_token = next(
                (c for c in cookies if c["name"] == "__Secure-next-auth.session-token"),
                None,
            )
            return session_token["value"] if session_token else None
        finally:
            await browser.close()


def login_and_get_cookie(email: str, password: str) -> str | None:
    try:
        return asyncio.run(_login(email, password))
    except Exception as e:
        log.error("Login failed for %s: %s", email, e)
        return None
