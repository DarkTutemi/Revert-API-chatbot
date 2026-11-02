import json

import httpx

from providers.base import BaseProvider, ChatMessage, UpstreamError

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"

MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]


class GeminiProvider(BaseProvider):
    name = "gemini"
    fallback_model = "gemini-2.5-flash"

    def __init__(self, api_key: str):
        self.api_key = api_key

    @staticmethod
    def build_payload(messages: list[ChatMessage],
                      temperature: float | None) -> dict:
        """
        OpenAI format → Gemini format.
        - system messages → systemInstruction (out of contents)
        - assistant role → model role
        """
        system = [m.content for m in messages if m.role == "system"]
        contents = []
        for m in messages:
            if m.role == "system":
                continue
            role = "model" if m.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        payload = {"contents": contents}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system)}]}
        if temperature is not None:
            payload["generationConfig"] = {"temperature": temperature}
        return payload

    def _headers(self) -> dict:
        # Header auth keeps the key out of URL/logs
        return {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

    def supports(self, model: str) -> bool:
        return model.startswith("gemini-")

    async def stream_chat(self, messages, model, temperature):
        url = f"{GEMINI_BASE}/models/{model}:streamGenerateContent?alt=sse"
        payload = self.build_payload(messages, temperature)

        async with httpx.AsyncClient(timeout=180) as client:
            async with client.stream(
                "POST", url, headers=self._headers(), json=payload
            ) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode(errors="replace")
                    raise UpstreamError(self.name, resp.status_code, body[:300])

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:].strip()
                    if not raw:
                        continue
                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    for cand in event.get("candidates", []):
                        for part in cand.get("content", {}).get("parts", []):
                            text = part.get("text")
                            if text:
                                yield text

    async def chat(self, messages, model, temperature) -> str:
        url = f"{GEMINI_BASE}/models/{model}:generateContent"
        payload = self.build_payload(messages, temperature)

        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(url, headers=self._headers(), json=payload)
            if resp.status_code != 200:
                raise UpstreamError(self.name, resp.status_code, resp.text[:300])
            data = resp.json()
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts)
