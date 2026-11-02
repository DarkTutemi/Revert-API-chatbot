import json

from core.sse_parser import openai_chunk, openai_completion


def test_role_frame():
    frame = json.loads(openai_chunk("gemini-2.5-flash"))
    assert frame["choices"][0]["delta"] == {"role": "assistant"}


def test_content_frame():
    frame = json.loads(openai_chunk("m", delta_content="hi"))
    assert frame["choices"][0]["delta"]["content"] == "hi"
    assert frame["choices"][0]["finish_reason"] is None


def test_completion_shape():
    body = openai_completion("m", "answer")
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["content"] == "answer"
