"""
Manual helper: extract __Secure-next-auth.session-token from a
logged-in browser session via Playwright, then optionally POST it
straight into the running proxy's /admin/add-account.
"""
import asyncio
import os
import sys
import httpx
from playwright.async_api import async_playwright


async def harvest_cookie(headless: bool = False) -> str | None:
    """Opens a browser; you log in manually; script grabs the cookie."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        print("[*] Opening chatgpt.com — log in, then come back here")
        await page.goto("https://chatgpt.com")

        # Poll until session cookie appears (you log in at your pace)
        for _ in range(600):  # 10 min
            cookies = await context.cookies()
            token = next(
                (c for c in cookies
                 if c["name"] == "__Secure-next-auth.session-token"),
                None,
            )
            if token:
                await browser.close()
                return token["value"]
            await asyncio.sleep(1)

        await browser.close()
        return None


async def push_to_proxy(cookie: str, proxy_url: str, api_key: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{proxy_url}/admin/add-account",
            headers={"x-api-key": api_key},
            json={"session_cookie": cookie},
        )
        print(f"[*] Proxy response: {resp.status_code} {resp.text}")


if __name__ == "__main__":
    proxy_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
    api_key = os.getenv("API_KEY", "change-me")

    cookie = asyncio.run(harvest_cookie())
    if cookie:
        print(f"[+] Got cookie: {cookie[:40]}...")
        asyncio.run(push_to_proxy(cookie, proxy_url, api_key))
    else:
        print("[-] Timed out waiting for login")
