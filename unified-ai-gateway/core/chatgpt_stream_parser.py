"""
ChatGPT Web SSE & Delta Parser for Unified AI Gateway.
Transforms proprietary OpenAI Web SSE frames into clean text deltas.
Handles both JSON-Patch (RFC 6902) updates and full message frames.
"""
import json
import logging

log = logging.getLogger("core.chatgpt_parser")


class ChatGPTStreamParser:
    def __init__(self):
        self.accumulated_text = ""
        self.initial_text_seen = False
        self.is_done = False

    def parse_chunk(self, raw_chunk: str) -> str:
        """
        Parses a raw SSE chunk from ChatGPT Web and returns the extracted delta text.
        Returns empty string if the chunk contains only metadata or ping events.
        """
        if not raw_chunk:
            return ""

        output_parts = []
        lines = raw_chunk.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Ignore SSE event headers
            if line.startswith("event:"):
                continue

            # Handle SSE data frames
            if line.startswith("data:"):
                data_str = line[5:].strip()
                if not data_str:
                    continue

                if data_str == "[DONE]":
                    self.is_done = True
                    break

                try:
                    event = json.loads(data_str)
                    delta = self._extract_delta(event)
                    if delta:
                        output_parts.append(delta)
                except Exception:
                    # Ignore unparseable non-json data frames
                    pass

        return "".join(output_parts)

    def _extract_delta(self, event: dict) -> str:
        if not isinstance(event, dict):
            return ""

        # 1. Standard OpenAI API format: {"choices": [{"delta": {"content": "..."}}]}
        if "choices" in event and isinstance(event["choices"], list) and event["choices"]:
            delta = event["choices"][0].get("delta", {})
            return delta.get("content", "")

        # 2. Modern ChatGPT Web JSON-Patch delta format (2025/2026):
        # {"o": "patch", "v": [{"p": "/message/content/parts/0", "o": "append", "v": "..."}]}
        # or {"v": [{"p": "/message/content/parts/0", "o": "append", "v": "..."}]}
        v_list = event.get("v")
        if isinstance(v_list, list):
            deltas = []
            for patch in v_list:
                if isinstance(patch, dict):
                    p = patch.get("p", "")
                    o = patch.get("o")
                    val = patch.get("v")
                    if "/message/content/parts/" in p and o == "append" and isinstance(val, str):
                        deltas.append(val)
                        self.accumulated_text += val
                    elif "/message/content/parts/" in p and o == "replace" and isinstance(val, str):
                        if val.startswith(self.accumulated_text):
                            diff = val[len(self.accumulated_text):]
                            self.accumulated_text = val
                            if diff:
                                deltas.append(diff)
                        else:
                            self.accumulated_text = val
                            deltas.append(val)
            return "".join(deltas)

        # 3. Modern initial assistant message frame:
        # {"p": "", "o": "add", "v": {"message": {"id": "...", "author": {"role": "assistant"}, "content": {"parts": ["Tao là"]}}}}
        # or {"v": {"message": {"author": {"role": "assistant"}, "content": {"parts": ["Tao là"]}}}}
        if isinstance(event.get("v"), dict):
            msg = event["v"].get("message", {})
            if msg.get("author", {}).get("role") == "assistant":
                parts = msg.get("content", {}).get("parts", [])
                if parts and isinstance(parts[0], str) and parts[0]:
                    initial_str = parts[0]
                    if not self.initial_text_seen:
                        self.initial_text_seen = True
                        self.accumulated_text = initial_str
                        return initial_str
                    elif initial_str.startswith(self.accumulated_text):
                        diff = initial_str[len(self.accumulated_text):]
                        self.accumulated_text = initial_str
                        return diff

        # 4. Legacy full message frame format:
        # {"message": {"author": {"role": "assistant"}, "content": {"parts": ["..."]}}}
        message = event.get("message")
        if isinstance(message, dict) and message.get("author", {}).get("role") == "assistant":
            parts = message.get("content", {}).get("parts", [])
            if parts and isinstance(parts[0], str) and parts[0]:
                full_text = parts[0]
                if full_text.startswith(self.accumulated_text):
                    diff = full_text[len(self.accumulated_text):]
                    self.accumulated_text = full_text
                    return diff
                else:
                    self.accumulated_text = full_text
                    return full_text

        # All other frames (metadata, tokens, markers) produce no visible text
        return ""
