import asyncio
import sys
import json
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

with open("H:/reqble-mcp/chatgpt-revert/scripts/test_eval_chat.py", "r", encoding="utf-8") as f:
    content = f.read()
    raw_cookie = content.split('raw_cookie = """')[1].split('"""')[0].strip()

async def test_real_chrome():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",  # Uses real installed Google Chrome!
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context()
        cookies = []
        for pair in raw_cookie.split(";"):
            if "=" in pair:
                k, v = pair.strip().split("=", 1)
                cookies.append({"name": k, "value": v, "url": "https://chatgpt.com/"})
        await ctx.add_cookies(cookies)
        
        page = await ctx.new_page()
        print("Navigating with real Chrome...")
        await page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # Test turnstile render
        token = await page.evaluate("""() => {
            return new Promise((resolve) => {
                const div = document.createElement('div');
                div.id = 'ts-container';
                document.body.appendChild(div);
                
                try {
                    window.turnstile.render('#ts-container', {
                        sitekey: '0x4AAAAAAADnPIDROrmt1Wwj',
                        callback: function(token) {
                            resolve({ success: true, token: token });
                        },
                        'error-callback': function(err) {
                            resolve({ success: false, error: err });
                        }
                    });
                    
                    setTimeout(() => resolve({ success: false, timeout: true }), 10000);
                } catch(e) {
                    resolve({ success: false, exception: e.message });
                }
            });
        }""")
        
        print("Real Chrome Turnstile result:", json.dumps(token, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_real_chrome())
