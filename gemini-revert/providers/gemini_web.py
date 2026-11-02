import asyncio
import logging
import uuid

from providers.base import BaseProvider, ChatMessage, UpstreamError
from api.routes_bridge import pending_jobs, active_job_queues
from core.gemini_stream_parser import extract_gemini_text

log = logging.getLogger("provider.gemini_web")


class GeminiWebProvider(BaseProvider):
    name = "gemini-web"
    fallback_model = "gemini-2.5-flash"

    def supports(self, model: str) -> bool:
        return True

    async def stream_chat(self, messages: list[ChatMessage], model: str, temperature: float | None):
        last_msg = messages[-1].content if messages else ""
        job_id = str(uuid.uuid4())
        job_queue = asyncio.Queue()
        active_job_queues[job_id] = job_queue

        import time
        await pending_jobs.put({
            "job_id": job_id,
            "prompt_text": last_msg,
            "model": model,
            "created_at": time.time(),
        })

        accumulated = ""
        try:
            while True:
                item = await asyncio.wait_for(job_queue.get(), timeout=60.0)

                if item.get("done"):
                    if accumulated:
                        break
                    log.warning("Received DONE for %s but accumulated text is empty, keeping stream open...", job_id)
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
            raise UpstreamError(self.name, 504, "Timeout waiting for Gemini tab bridge response")
        finally:
            active_job_queues.pop(job_id, None)

    async def chat(self, messages: list[ChatMessage], model: str, temperature: float | None) -> str:
        parts = []
        async for delta in self.stream_chat(messages, model, temperature):
            parts.append(delta)
        return "".join(parts)
