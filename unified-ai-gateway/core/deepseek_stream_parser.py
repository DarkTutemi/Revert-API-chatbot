"""
DeepSeek Web SSE & Chunk Parser.
Formats raw DeepSeek SSE frames into OpenAI-compatible text deltas.
Handles DeepSeek-R1 thinking chunks via <think>...</think> tags.
"""
import json
import logging

log = logging.getLogger("core.deepseek_parser")


class DeepSeekStreamParser:
    def __init__(self):
        self.thinking_started = False
        self.thinking_ended = False

    def parse_chunk(self, raw: str) -> str:
        if not raw:
            return ""

        output_parts = []
        lines = raw.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("event:"):
                continue
            if line.startswith("data:"):
                line = line[5:].strip()

            if line == "[DONE]":
                if self.thinking_started and not self.thinking_ended:
                    output_parts.append("\n</think>\n\n")
                    self.thinking_ended = True
                continue

            try:
                data = json.loads(line)
                delta_text = self._extract_content(data)
                if delta_text:
                    output_parts.append(delta_text)
            except Exception:
                # If it's a plaintext chunk (e.g. from DOM fallback)
                if not line.startswith("{") and not line.startswith("data:"):
                    output_parts.append(line)

        return "".join(output_parts)

    def _extract_content(self, data: dict) -> str:
        res = []

        if "v" in data and isinstance(data["v"], dict):
            resp = data["v"].get("response") or {}
            msg_type = resp.get("type", "text")
            content = resp.get("content", "")

            if msg_type == "thinking" and content:
                if not self.thinking_started:
                    res.append("<think>\n")
                    self.thinking_started = True
                res.append(content)
            elif msg_type == "text" and content:
                if self.thinking_started and not self.thinking_ended:
                    res.append("\n</think>\n\n")
                    self.thinking_ended = True
                res.append(content)

        elif "choices" in data and isinstance(data["choices"], list) and data["choices"]:
            delta = data["choices"][0].get("delta", {})
            reasoning = delta.get("reasoning_content") or delta.get("thinking")
            text = delta.get("content", "")

            if reasoning:
                if not self.thinking_started:
                    res.append("<think>\n")
                    self.thinking_started = True
                res.append(reasoning)

            if text:
                if self.thinking_started and not self.thinking_ended:
                    res.append("\n</think>\n\n")
                    self.thinking_ended = True
                res.append(text)

        elif "content" in data:
            res.append(str(data["content"]))

        return "".join(res)
