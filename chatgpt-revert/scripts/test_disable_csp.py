import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def test_csp():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-web-security",
                "--disable-site-isolation-trials"
            ]
        )
        page = await browser.new_page()
        await page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        
        # Test fetch to localhost:3000
        res = await page.evaluate("""async () => {
            try {
                const r = await fetch("http://localhost:3000/bridge/status");
                const data = await r.json();
                return { success: true, data };
            } catch (e) {
                return { success: false, error: e.message };
            }
        }""")
        
        print("Fetch result from chatgpt.com to localhost with --disable-web-security:")
        print(res)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_csp())
