from providers.openai_compat import OpenAICompatProvider

GROQ_BASE = "https://api.groq.com/openai/v1"

MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


class GroqProvider(OpenAICompatProvider):
    name = "groq"
    fallback_model = "llama-3.3-70b-versatile"

    def __init__(self, api_key: str):
        super().__init__(api_key, GROQ_BASE)

    def supports(self, model: str) -> bool:
        return model.startswith(("llama-", "gemma-", "mixtral-"))
