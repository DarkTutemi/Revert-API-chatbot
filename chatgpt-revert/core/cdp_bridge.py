"""
Chrome DevTools Protocol (CDP) Bridge for real browser streaming.
Connects to paneer's active Chrome instance on port 9222.
"""
import asyncio
import json
import logging
import urllib.request
from playwright.async_api import async_playwright

from config import Config
from core.sse_parser import openai_chunk

log = logging.getLogger("core.cdp")


def is_cdp_available() -> bool:
    try:
        with urllib.request.urlopen(f"{Config.CDP_URL}/json/version", timeout=1) as resp:
            return resp.status == 200
    except Exception:
        return False


async def stream_via_cdp(payload: dict, access_token: str, model: str):
    """
    Evaluates fetch stream inside paneer's real Chrome ChatGPT tab.
    Bypasses Cloudflare Turnstile & Sentinel checks natively.
    """
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(Config.CDP_URL)
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        
        chatgpt_page = None
        for page in context.pages:
            if "chatgpt.com" in page.url:
                chatgpt_page = page
                break
                
        if not chatgpt_page:
            chatgpt_page = await context.new_page()
            await chatgpt_page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
            await asyncio.sleep(2)

        # First frame
        yield f"data: {openai_chunk(model)}\n\n"

        # Expose Python chunk collector to JavaScript
        queue = asyncio.Queue()

        await chatgpt_page.expose_binding(
            "__on_stream_chunk",
            lambda source, chunk: queue.put_nowait(chunk)
        )

        # Trigger in-page stream
        eval_task = asyncio.create_task(chatgpt_page.evaluate("""async (args) => {
            const { payload, token } = args;
            
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
            
            const headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
                "chatgpt-account-id": "83f209d0-1b7e-4f54-8d1e-24afbf7b6e94",
                "openai-sentinel-chat-requirements-token": reqData.token || ""
            };
            
            const resp = await fetch("/backend-api/f/conversation", {
                method: "POST",
                headers: headers,
                body: JSON.stringify(payload)
            });
            
            if (resp.status !== 200) {
                const errText = await resp.text();
                await window.__on_stream_chunk({ error: errText, status: resp.status });
                await window.__on_stream_chunk({ done: true });
                return;
            }
            
            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunkStr = decoder.decode(value, { stream: true });
                await window.__on_stream_chunk({ chunk: chunkStr });
            }
            await window.__on_stream_chunk({ done: true });
        }""", {"payload": payload, "token": access_token}))

        accumulated_text = ""
        while True:
            item = await queue.get()
            if item.get("done"):
                break
            if item.get("error"):
                log.error("CDP in-page stream error: %s", item.get("error"))
                yield f"data: {json.dumps({'error': {'message': item.get('error')}})}\n\n"
                break
            
            raw_chunk = item.get("chunk", "")
            for line in raw_chunk.splitlines():
                line = line.strip()
                if not line.startswith("data: "):
                    continue
                data_part = line[6:]
                if data_part == "[DONE]":
                    continue
                try:
                    obj = json.loads(data_part)
                    parts = obj.get("message", {}).get("content", {}).get("parts", [])
                    if parts and isinstance(parts[0], str):
                        full_msg = parts[0]
                        delta = full_msg[len(accumulated_text):]
                        accumulated_text = full_msg
                        if delta:
                            yield f"data: {openai_chunk(model, delta_content=delta)}\n\n"
                except Exception:
                    pass

        yield f"data: {openai_chunk(model, finish_reason='stop')}\n\n"
        yield "data: [DONE]\n\n"
        await eval_task
