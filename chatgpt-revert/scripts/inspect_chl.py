import asyncio
import sys
import json
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

with open("H:/reqble-mcp/chatgpt-revert/scripts/test_eval_chat.py", "r", encoding="utf-8") as f:
    content = f.read()
    raw_cookie = content.split('raw_cookie = """')[1].split('"""')[0].strip()

async def inspect():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context()
        cookies = []
        for pair in raw_cookie.split(";"):
            if "=" in pair:
                k, v = pair.strip().split("=", 1)
                cookies.append({"name": k, "value": v, "url": "https://chatgpt.com/"})
        await ctx.add_cookies(cookies)
        page = await ctx.new_page()
        await page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        res = await page.evaluate("() => window._cf_chl_opt || null")
        print("CHL OPT:", json.dumps(res, indent=2))
        await b.close()

if __name__ == "__main__":
    asyncio.run(inspect())
