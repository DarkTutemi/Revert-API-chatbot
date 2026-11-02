import json

import httpx

from providers.base import BaseProvider, UpstreamError


class OpenAICompatProvider(BaseProvider):
    """Base for providers that already speak the OpenAI wire format (Groq, OpenRouter)."""

    def __init__(self, api_key: str, base_url: str, extra_headers: dict | None = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.extra_headers = extra_headers or {}

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers,
        }

    @staticmethod
    def _payload(messages, model, temperature) -> dict:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if temperature is not None:
            payload["temperature"] = temperature
        return payload

    def supports(self, model: str) -> bool:
        return False  # subclasses override

    async def stream_chat(self, messages, model, temperature):
        async with httpx.AsyncClient(timeout=180) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={**self._payload(messages, model, temperature), "stream": True},
            ) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode(errors="replace")
                    raise UpstreamError(self.name, resp.status_code, body[:300])

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        chunk = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    for choice in chunk.get("choices", []):
                        text = choice.get("delta", {}).get("content")
                        if text:
                            yield text

    async def chat(self, messages, model, temperature) -> str:
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=self._payload(messages, model, temperature),
            )
            if resp.status_code != 200:
                raise UpstreamError(self.name, resp.status_code, resp.text[:300])
            return resp.json()["choices"][0]["message"]["content"]
