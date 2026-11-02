import asyncio
import sys
import json
import uuid
import time
sys.path.insert(0, "H:/reqble-mcp/chatgpt-revert")
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
        res = await page.evaluate("""async (args) => {
            const { token, conv_id } = args;
            
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
            
            return {
                token: reqData.token,
                pow: reqData.proofofwork,
                turnstile: reqData.turnstile
            };
        }""", {"token": access_token})
        
        from core.sentinel import solve_openai_pow
        pow_info = res.get("pow", {})
        proof_token = solve_openai_pow(pow_info.get("seed"), pow_info.get("difficulty"))
        print("Solved PoW:", proof_token[:40], "...")
        
        # Now call conversation from inside page!
        conv_res = await page.evaluate("""async (args) => {
            const { token, reqToken, proofToken } = args;
            
            const payload = {
                turn_attribution: { turn_trigger: "composer" },
                action: "next",
                messages: [{
                    id: crypto.randomUUID(),
                    author: { role: "user" },
                    content: { content_type: "text", parts: ["1+1 bang may?"] }
                }],
                parent_message_id: crypto.randomUUID(),
                model: "auto",
                timezone: "Asia/Saigon",
                timezone_offset_min: -420,
                history_and_training_disabled: true
            };
            
            const headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
                "chatgpt-account-id": "83f209d0-1b7e-4f54-8d1e-24afbf7b6e94",
                "openai-sentinel-chat-requirements-token": reqToken,
                "openai-sentinel-proof-token": proofToken
            };
            
            const resp = await fetch("/backend-api/f/conversation", {
                method: "POST",
                headers: headers,
                body: JSON.stringify(payload)
            });
            
            const status = resp.status;
            let text = "";
            if (status === 200) {
                const reader = resp.body.getReader();
                const decoder = new TextDecoder();
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    text += decoder.decode(value);
                    if (text.length > 500) break;
                }
            } else {
                text = await resp.text();
            }
            
            return { status, text: text.slice(0, 300) };
        }""", {
            "token": access_token,
            "reqToken": res.get("token"),
            "proofToken": proof_token
        })
        
        print("Conversation result from browser page:", json.dumps(conv_res, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
