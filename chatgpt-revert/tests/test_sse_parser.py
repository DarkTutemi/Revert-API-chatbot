import json
from core.sse_parser import (
    parse_sse_line,
    extract_assistant_text,
    compute_delta,
    openai_chunk,
)


def test_parse_sse_line_valid():
    line = 'data: {"conversation_id": "abc"}'
    assert parse_sse_line(line) == {"conversation_id": "abc"}


def test_parse_sse_line_done():
    assert parse_sse_line("data: [DONE]") is None


def test_parse_sse_line_not_data():
    assert parse_sse_line("event: message") is None


def test_parse_sse_line_invalid_json():
    assert parse_sse_line("data: not-json{") is None


def test_extract_assistant_text():
    event = {
        "message": {
            "id": "msg_123",
            "author": {"role": "assistant"},
            "content": {"content_type": "text", "parts": ["hello world"]},
            "metadata": {},
        }
    }
    text, msg_id = extract_assistant_text(event)
    assert text == "hello world"
    assert msg_id == "msg_123"


def test_extract_ignores_user_messages():
    event = {
        "message": {
            "author": {"role": "user"},
            "content": {"content_type": "text", "parts": ["hi"]},
        }
    }
    assert extract_assistant_text(event) == (None, None)


def test_compute_delta_normal():
    assert compute_delta("hello", "hello world") == " world"


def test_compute_delta_rewrite():
    assert compute_delta("abc", "xyz") == "xyz"


def test_openai_chunk_shape():
    frame = json.loads(openai_chunk("gpt-4o", delta_content="hi"))
    assert frame["object"] == "chat.completion.chunk"
    assert frame["choices"][0]["delta"]["content"] == "hi"
    assert frame["choices"][0]["finish_reason"] is None
