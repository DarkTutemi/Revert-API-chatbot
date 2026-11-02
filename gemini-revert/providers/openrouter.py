from providers.openai_compat import OpenAICompatProvider

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
]


class OpenRouterProvider(OpenAICompatProvider):
    name = "openrouter"
    fallback_model = "meta-llama/llama-3.3-70b-instruct:free"

    def __init__(self, api_key: str):
        super().__init__(
            api_key,
            OPENROUTER_BASE,
            extra_headers={
                "HTTP-Referer": "https://localhost",
                "X-Title": "gemini-gateway",
            },
        )

    def supports(self, model: str) -> bool:
        return "/" in model  # OpenRouter model ids are vendor/name
