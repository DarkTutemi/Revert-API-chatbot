from providers.gemini import GeminiProvider
from providers.base import ChatMessage
from providers import ALIASES, _home_provider


def test_system_message_becomes_system_instruction():
    msgs = [
        ChatMessage(role="system", content="be terse"),
        ChatMessage(role="user", content="hi"),
        ChatMessage(role="assistant", content="hello"),
        ChatMessage(role="user", content="bye"),
    ]
    payload = GeminiProvider.build_payload(msgs, 0.7)
    assert payload["systemInstruction"]["parts"][0]["text"] == "be terse"
    roles = [c["role"] for c in payload["contents"]]
    assert roles == ["user", "model", "user"]
    assert payload["generationConfig"]["temperature"] == 0.7


def test_no_system_no_config():
    payload = GeminiProvider.build_payload(
        [ChatMessage(role="user", content="x")], None
    )
    assert "systemInstruction" not in payload
    assert "generationConfig" not in payload


def test_alias_and_home_routing():
    assert ALIASES["gpt-4o"] == "gemini-2.5-flash"
    assert _home_provider("gemini-2.5-pro") == "gemini"
    assert _home_provider("llama-3.3-70b-versatile") == "groq"
    assert _home_provider("meta-llama/llama-3.3-70b-instruct:free") == "openrouter"
