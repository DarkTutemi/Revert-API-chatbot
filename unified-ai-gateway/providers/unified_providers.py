import asyncio
import json
import logging
import time
import uuid

from providers.base import BaseProvider, ChatMessage, UpstreamError
from api.routes_bridge import pending_jobs, active_job_queues
from core.chatgpt_stream_parser import ChatGPTStreamParser
from core.gemini_stream_parser import extract_gemini_text
from core.deepseek_stream_parser import DeepSeekStreamParser

log = logging.getLogger("provider.unified")


class ChatGPTWebProvider(BaseProvider):
    name = "chatgpt-web"

    async def stream_chat(self, messages: list[ChatMessage], model: str, temperature: float | None):
        last_msg = messages[-1].content if messages else ""
        job_id = str(uuid.uuid4())
        job_queue = asyncio.Queue()
        active_job_queues[job_id] = job_queue

        await pending_jobs["chatgpt"].put({
            "job_id": job_id,
            "prompt_text": last_msg,
            "model": model,
            "provider": "chatgpt",
            "created_at": time.time(),
        })

        parser = ChatGPTStreamParser()
        accumulated = ""
        try:
            while True:
                item = await asyncio.wait_for(job_queue.get(), timeout=90.0)
                if item.get("done") or parser.is_done:
                    break
                if item.get("error"):
                    raise UpstreamError(self.name, 502, item["error"])

                raw_chunk = item.get("chunk", "")
                if raw_chunk:
                    delta = parser.parse_chunk(raw_chunk)
                    if delta:
                        accumulated += delta
                        yield delta
                if parser.is_done:
                    break
        except asyncio.TimeoutError:
            raise UpstreamError(self.name, 504, "Timeout waiting for ChatGPT tab response")
        finally:
            active_job_queues.pop(job_id, None)

    async def chat(self, messages: list[ChatMessage], model: str, temperature: float | None) -> str:
        parts = []
        async for d in self.stream_chat(messages, model, temperature):
            parts.append(d)
        return "".join(parts)


class GeminiWebProvider(BaseProvider):
    name = "gemini-web"

    async def stream_chat(self, messages: list[ChatMessage], model: str, temperature: float | None):
        last_msg = messages[-1].content if messages else ""
        job_id = str(uuid.uuid4())
        job_queue = asyncio.Queue()
        active_job_queues[job_id] = job_queue

        await pending_jobs["gemini"].put({
            "job_id": job_id,
            "prompt_text": last_msg,
            "model": model,
            "provider": "gemini",
            "created_at": time.time(),
        })

        accumulated = ""
        try:
            while True:
                item = await asyncio.wait_for(job_queue.get(), timeout=90.0)
                if item.get("done"):
                    if accumulated:
                        break
                    continue
                if item.get("error"):
                    raise UpstreamError(self.name, 502, item["error"])

                raw_chunk = item.get("chunk", "")
                if raw_chunk:
                    text = extract_gemini_text(raw_chunk)
                    if text:
                        if text.startswith(accumulated):
                            delta = text[len(accumulated):]
                            accumulated = text
                        else:
                            delta = text
                            accumulated += text
                        if delta:
                            yield delta
        except asyncio.TimeoutError:
            raise UpstreamError(self.name, 504, "Timeout waiting for Gemini tab response")
        finally:
            active_job_queues.pop(job_id, None)

    async def chat(self, messages: list[ChatMessage], model: str, temperature: float | None) -> str:
        parts = []
        async for d in self.stream_chat(messages, model, temperature):
            parts.append(d)
        return "".join(parts)


class DeepSeekWebProvider(BaseProvider):
    name = "deepseek-web"

    async def stream_chat(self, messages: list[ChatMessage], model: str, temperature: float | None):
        last_msg = messages[-1].content if messages else ""
        job_id = str(uuid.uuid4())
        job_queue = asyncio.Queue()
        active_job_queues[job_id] = job_queue

        await pending_jobs["deepseek"].put({
            "job_id": job_id,
            "prompt_text": last_msg,
            "model": model,
            "provider": "deepseek",
            "created_at": time.time(),
        })

        parser = DeepSeekStreamParser()
        accumulated = ""
        try:
            while True:
                item = await asyncio.wait_for(job_queue.get(), timeout=90.0)
                if item.get("done"):
                    if parser.thinking_started and not parser.thinking_ended:
                        yield "\n</think>\n\n"
                        parser.thinking_ended = True
                    break
                if item.get("error"):
                    raise UpstreamError(self.name, 502, item["error"])

                raw_chunk = item.get("chunk", "")
                if raw_chunk:
                    delta = parser.parse_chunk(raw_chunk)
                    if delta:
                        accumulated += delta
                        yield delta
        except asyncio.TimeoutError:
            raise UpstreamError(self.name, 504, "Timeout waiting for DeepSeek tab response")
        finally:
            active_job_queues.pop(job_id, None)

    async def chat(self, messages: list[ChatMessage], model: str, temperature: float | None) -> str:
        parts = []
        async for d in self.stream_chat(messages, model, temperature):
            parts.append(d)
        return "".join(parts)


class UnifiedRouter:
    def __init__(self):
        self.chatgpt = ChatGPTWebProvider()
        self.gemini = GeminiWebProvider()
        self.deepseek = DeepSeekWebProvider()

    def resolve_provider(self, model: str) -> BaseProvider:
        m = (model or "").lower()
        if "gemini" in m:
            return self.gemini
        if "deepseek" in m or "r1" in m or "v3" in m:
            return self.deepseek
        if "gpt" in m or "chatgpt" in m or "o1" in m:
            return self.chatgpt
        # Default to deepseek if unspecified
        return self.deepseek

    async def stream(self, messages: list[ChatMessage], model: str, temperature: float | None):
        provider = self.resolve_provider(model)
        log.info("Routing model '%s' -> %s", model, provider.name)
        async for chunk in provider.stream_chat(messages, model, temperature):
            yield chunk

    async def chat(self, messages: list[ChatMessage], model: str, temperature: float | None) -> str:
        provider = self.resolve_provider(model)
        log.info("Routing model '%s' -> %s", model, provider.name)
        return await provider.chat(messages, model, temperature)
