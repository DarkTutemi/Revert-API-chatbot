"""
Transform ChatGPT's SSE stream into OpenAI-format chunks.

Supports both legacy accumulated message format and modern
JSON patch delta format (o: "patch", v: [{"p": ..., "o": "append", "v": ...}]).
"""
import json
import time
import uuid


def parse_sse_line(line: str) -> dict | None:
    """Parse one SSE line -> dict, or None if not a valid dict."""
    if not line.startswith("data: "):
        return None
    data_str = line[6:].strip()
    if not data_str or data_str == "[DONE]":
        return None
    try:
        val = json.loads(data_str)
        if isinstance(val, dict):
            return val
        return None
    except json.JSONDecodeError:
        return None


def extract_assistant_text(event: dict) -> tuple[str | None, str | None, bool]:
    """
    Returns (text, message_id, is_delta).
    If is_delta is True: text is the direct delta chunk.
    If is_delta is False: text is the accumulated full text so far.
    """
    if not isinstance(event, dict):
        return None, None, False

    # 1. Modern patch delta format (2025/2026)
    # e.g. {"v": [{"p": "/message/content/parts/0", "o": "append", "v": "text"}]}
    v_list = event.get("v")
    if isinstance(v_list, list):
        for patch in v_list:
            if isinstance(patch, dict):
                p = patch.get("p", "")
                o = patch.get("o")
                val = patch.get("v")
                if "/message/content/parts/" in p and o == "append" and isinstance(val, str):
                    return val, None, True
                elif "/message/content/parts/" in p and o == "replace" and isinstance(val, str):
                    return val, None, False

    # 2. Modern initial add event
    # e.g. {"p": "", "o": "add", "v": {"message": {"id": "...", "author": {"role": "assistant"} ...}}}
    if isinstance(event.get("v"), dict):
        msg = event["v"].get("message", {})
        if msg.get("author", {}).get("role") == "assistant":
            parts = msg.get("content", {}).get("parts", [])
            initial_text = parts[0] if parts and isinstance(parts[0], str) else ""
            return initial_text, msg.get("id"), False

    # 3. Legacy full message format
    message = event.get("message")
    if isinstance(message, dict):
        if message.get("author", {}).get("role") != "assistant":
            return None, None, False
        metadata = message.get("metadata", {})
        if metadata.get("is_visited_conversation"):
            return None, message.get("id"), False
        content = message.get("content", {})
        if content.get("content_type") != "text":
            return None, message.get("id"), False
        parts = content.get("parts", [])
        if parts and isinstance(parts[0], str):
            return parts[0], message.get("id"), False

    return None, None, False


def compute_delta(previous: str, accumulated: str) -> str:
    """ChatGPT sends the full text each time — emit only the new suffix."""
    if accumulated.startswith(previous):
        return accumulated[len(previous):]
    return accumulated


def openai_chunk(model: str, delta_content: str | None = None,
                 finish_reason: str | None = None) -> str:
    """Build one OpenAI chat.completion.chunk SSE frame."""
    delta = {}
    if delta_content is not None:
        delta["content"] = delta_content
    if delta_content is None and finish_reason is None:
        delta["role"] = "assistant"  # first frame carries the role

    return json.dumps({
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "delta": delta,
            "finish_reason": finish_reason,
        }],
    })


def openai_completion(model: str, full_text: str) -> dict:
    """Non-streaming response body."""
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": full_text},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
