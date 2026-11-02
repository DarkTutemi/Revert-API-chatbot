import asyncio
import logging
import time
import uuid

from providers.base import BaseProvider, ChatMessage, UpstreamError
from api.routes_bridge import pending_jobs, active_job_queues
from core.deepseek_stream_parser import DeepSeekStreamParser

log = logging.getLogger("provider.deepseek_web")


class DeepSeekWebProvider(BaseProvider):
    name = "deepseek-web"
    fallback_model = "deepseek-reasoner"

    def supports(self, model: str) -> bool:
        return True

    async def stream_chat(self, messages: list[ChatMessage], model: str, temperature: float | None):
        last_msg = messages[-1].content if messages else ""
        job_id = str(uuid.uuid4())
        job_queue = asyncio.Queue()
        active_job_queues[job_id] = job_queue

        await pending_jobs.put({
            "job_id": job_id,
            "prompt_text": last_msg,
            "model": model,
            "created_at": time.time(),
        })

        parser = DeepSeekStreamParser()
        accumulated = ""

        try:
            while True:
                item = await asyncio.wait_for(job_queue.get(), timeout=90.0)

                if item.get("done"):
                    # Check if thinking was open and close it
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
            raise UpstreamError(self.name, 504, "Timeout waiting for DeepSeek tab bridge response")
        finally:
            active_job_queues.pop(job_id, None)

    async def chat(self, messages: list[ChatMessage], model: str, temperature: float | None) -> str:
        parts = []
        async for delta in self.stream_chat(messages, model, temperature):
            parts.append(delta)
        return "".join(parts)
