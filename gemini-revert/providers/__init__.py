import logging

from providers.base import BaseProvider, ChatMessage, UpstreamError
from providers.gemini import GeminiProvider
from providers.gemini_web import GeminiWebProvider
from providers.groq import GroqProvider
from providers.openrouter import OpenRouterProvider

log = logging.getLogger("router")

# Old OpenAI-style names keep working out of habit
ALIASES = {
    "gpt-4o": "gemini-2.5-flash",
    "gpt-4o-mini": "gemini-2.5-flash-lite",
    "gpt-4": "gemini-2.5-pro",
    "gpt-3.5-turbo": "gemini-2.0-flash",
}

PREFIX_HOME = [
    ("gemini-", "gemini"),
    ("llama-", "groq"),
    ("gemma-", "groq"),
    ("mixtral-", "groq"),
]


def _home_provider(model: str) -> str | None:
    for prefix, provider in PREFIX_HOME:
        if model.startswith(prefix):
            return provider
    if "/" in model:
        return "openrouter"
    return None


class ProviderRouter:
    """
    Resolves model → ordered provider chain, then serves with failover.
    Chain = home provider of the model (if configured) + PROVIDER_ORDER rest.
    Failover only fires BEFORE the first delta — mid-stream switch would
    duplicate text already sent to the client.
    """

    def __init__(self, providers: dict[str, BaseProvider],
                 default_order: list[str], default_model: str):
        self.providers = providers
        self.order = default_order
        self.default_model = default_model

    def resolve(self, model: str | None) -> list[tuple[BaseProvider, str]]:
        model = (model or "").strip()
        if model in ALIASES:
            model = ALIASES[model]
        if not model:
            model = self.default_model

        chain: list[tuple[BaseProvider, str]] = []
        home = _home_provider(model)
        if home and home in self.providers:
            p = self.providers[home]
            if p.supports(model):
                chain.append((p, model))

        for name in self.order:
            p = self.providers.get(name)
            if p and all(q.name != name for q, _ in chain):
                chain.append((p, p.fallback_model))

        if not chain:
            raise UpstreamError("router", 400, f"no provider can serve model: {model}")
        return chain

    async def chat(self, messages, model, temperature) -> str:
        last_error: UpstreamError | None = None
        for provider, mapped in self.resolve(model):
            try:
                text = await provider.chat(messages, mapped, temperature)
                log.info("model=%s → %s (%s)", model, provider.name, mapped)
                return text
            except UpstreamError as e:
                last_error = e
                if not e.retryable:
                    raise
                log.warning("%s failed (%s) — failing over", e.provider, e.status)
        raise last_error

    async def stream(self, messages, model, temperature):
        started = False
        last_error: UpstreamError | None = None
        for provider, mapped in self.resolve(model):
            try:
                async for delta in provider.stream_chat(messages, mapped, temperature):
                    started = True
                    yield delta
                return
            except UpstreamError as e:
                last_error = e
                if started or not e.retryable:
                    raise
                log.warning("%s failed (%s) — failing over", e.provider, e.status)
        raise last_error
