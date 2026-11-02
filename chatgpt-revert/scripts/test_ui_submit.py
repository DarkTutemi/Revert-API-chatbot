import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

with open("H:/reqble-mcp/chatgpt-revert/scripts/test_eval_chat.py", "r", encoding="utf-8") as f:
    content = f.read()
    raw_cookie = content.split('raw_cookie = """')[1].split('"""')[0].strip()

async def test_ui():
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
        page.on("request", lambda req: print(f">> [{req.method}] {req.url}") if "conversation" in req.url else None)
        page.on("response", lambda res: print(f"<< [{res.status}] {res.url}") if "conversation" in res.url else None)
        
        print("Navigating to chatgpt.com...")
        await page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        await asyncio.sleep(4)
        
        # Click on prompt area
        prompt_box = page.locator("#prompt-textarea, #pending-home-input, div[contenteditable='true']").first
        if await prompt_box.count() > 0:
            print("Clicking prompt box...")
            await prompt_box.click()
            await asyncio.sleep(0.5)
            print("Typing message...")
            await page.keyboard.type("1+1=? Chi tra loi con so.")
            await asyncio.sleep(1)
            
            # Find send button
            send_btn = page.locator("button[data-testid='send-button'], button[aria-label*='Send'], button[aria-label*='Gửi']").first
            if await send_btn.count() > 0:
                print("Clicking Send button...")
                await send_btn.click()
            else:
                print("Send button not found, pressing Enter...")
                await page.keyboard.press("Enter")
                
            # Wait for assistant response
            for i in range(15):
                await asyncio.sleep(1)
                msgs = await page.locator("div[data-message-author-role='assistant']").all_text_contents()
                if msgs:
                    print(f"Assistant response received ({len(msgs)} messages):")
                    print("Last message:", msgs[-1].strip())
                    break
        else:
            print("No prompt box found.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_ui())
