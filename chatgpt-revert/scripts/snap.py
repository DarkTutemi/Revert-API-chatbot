import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

with open("H:/reqble-mcp/chatgpt-revert/scripts/test_eval_chat.py", "r", encoding="utf-8") as f:
    content = f.read()
    raw_cookie = content.split('raw_cookie = """')[1].split('"""')[0].strip()

async def snap():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        cookies = []
        for pair in raw_cookie.split(";"):
            if "=" in pair:
                k, v = pair.strip().split("=", 1)
                cookies.append({"name": k, "value": v, "url": "https://chatgpt.com/"})
        await ctx.add_cookies(cookies)
        page = await ctx.new_page()
        await page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        await asyncio.sleep(4)
        print("Current URL:", page.url)
        print("Page title:", await page.title())
        await page.screenshot(path="H:/reqble-mcp/chatgpt-revert/page_snap.png")
        print("Screenshot saved to H:/reqble-mcp/chatgpt-revert/page_snap.png")
        await b.close()

if __name__ == "__main__":
    asyncio.run(snap())
