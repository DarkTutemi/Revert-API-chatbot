import asyncio
import sys
import json
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    print("Connecting to Chrome on port 9222...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected successfully to Chrome!")
            contexts = browser.contexts
            if not contexts:
                print("No browser contexts found.")
                return
            
            context = contexts[0]
            pages = context.pages
            print(f"Total open tabs: {len(pages)}")
            
            # Find ChatGPT page
            chatgpt_page = None
            for page in pages:
                url = page.url
                print("Tab URL:", url)
                if "chatgpt.com" in url:
                    chatgpt_page = page
                    break
                    
            if not chatgpt_page:
                print("ChatGPT tab not found, navigating first tab to https://chatgpt.com/...")
                chatgpt_page = await context.new_page()
                await chatgpt_page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
                await asyncio.sleep(2)
            else:
                print("Found existing ChatGPT tab!")
                
            print("ChatGPT tab title:", await chatgpt_page.title())
            
            # Test in-page conversation call directly via CDP
            access_token = open("H:/reqble-mcp/chatgpt-revert/accounts.txt").read().strip()
            
            print("Testing in-page stream through Chrome CDP...")
            stream_result = await chatgpt_page.evaluate("""async (token) => {
                // 1. Requirements
                const reqRes = await fetch("/backend-api/sentinel/chat-requirements", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": "Bearer " + token,
                        "chatgpt-account-id": "83f209d0-1b7e-4f54-8d1e-24afbf7b6e94"
                    },
                    body: "{}"
                });
                const reqData = await reqRes.json();
                return { status: reqRes.status, reqData };
            }""", access_token)
            
            print("CDP chat-requirements result:", json.dumps(stream_result, indent=2)[:300])
        except Exception as e:
            print("CDP connection error:", e)

if __name__ == "__main__":
    asyncio.run(main())
