import json
import time
import uuid


def openai_chunk(model: str, delta_content: str | None = None,
                 finish_reason: str | None = None) -> str:
    """One OpenAI chat.completion.chunk SSE frame."""
    delta = {}
    if delta_content is not None:
        delta["content"] = delta_content
    if delta_content is None and finish_reason is None:
        delta["role"] = "assistant"
    return json.dumps({
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    })


def openai_completion(model: str, full_text: str) -> dict:
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
