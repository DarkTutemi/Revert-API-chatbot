import asyncio
import sys
import json
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

with open("H:/reqble-mcp/chatgpt-revert/scripts/test_eval_chat.py", "r", encoding="utf-8") as f:
    content = f.read()
    raw_cookie = content.split('raw_cookie = """')[1].split('"""')[0].strip()

access_token = open("H:/reqble-mcp/chatgpt-revert/accounts.txt").read().strip()

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        
        cookies = []
        for pair in raw_cookie.split(";"):
            if "=" in pair:
                k, v = pair.strip().split("=", 1)
                cookies.append({"name": k, "value": v, "url": "https://chatgpt.com/"})
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        await page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        
        # Test in-page fetch of conversation
        res = await page.evaluate("""async (token) => {
            // 1. Chat requirements
            const reqRes = await fetch("/backend-api/sentinel/chat-requirements", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + token,
                    "chatgpt-account-id": "83f209d0-1b7e-4f54-8d1e-24afbf7b6e94",
                    "OAI-Language": "vi-VN"
                },
                body: "{}"
            });
            const reqData = await reqRes.json();
            
            // Look for turnstile in window or DOM
            let turnstileToken = "";
            const turnstileInput = document.querySelector('input[name="cf-turnstile-response"]');
            if (turnstileInput) turnstileToken = turnstileInput.value;
            
            return {
                status: reqRes.status,
                token: reqData.token,
                pow: reqData.proofofwork,
                turnstile: reqData.turnstile,
                domTurnstile: turnstileToken,
                hasTurnstileApi: typeof window.turnstile !== "undefined"
            };
        }""", access_token)
        
        print("Page evaluation:", json.dumps(res, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
