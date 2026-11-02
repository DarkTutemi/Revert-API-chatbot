import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

with open("H:/reqble-mcp/chatgpt-revert/scripts/test_eval_chat.py", "r", encoding="utf-8") as f:
    content = f.read()
    raw_cookie = content.split('raw_cookie = """')[1].split('"""')[0].strip()

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        cookies = []
        for pair in raw_cookie.split(";"):
            if "=" in pair:
                k, v = pair.strip().split("=", 1)
                cookies.append({"name": k, "value": v, "url": "https://chatgpt.com/"})
        await ctx.add_cookies(cookies)
        page = await ctx.new_page()
        await page.goto("https://chatgpt.com/", wait_until="networkidle")
        
        # Print all interactive elements
        elements = await page.locator("textarea, input, [contenteditable='true'], div[id*='input'], div[class*='ProseMirror']").all()
        print(f"Total found: {len(elements)}")
        for i, el in enumerate(elements):
            tag = await el.evaluate("e => e.tagName")
            id_ = await el.get_attribute("id")
            cls = await el.get_attribute("class")
            ph = await el.get_attribute("placeholder")
            print(f"[{i}] {tag} id={id_} placeholder={ph} class={cls[:40] if cls else ''}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check())
