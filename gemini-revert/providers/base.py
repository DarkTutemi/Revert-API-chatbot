from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str
    content: str


class UpstreamError(Exception):
    """Provider call failed — carries status for failover decisions."""

    def __init__(self, provider: str, status: int, message: str):
        self.provider = provider
        self.status = status
        self.message = message
        super().__init__(f"[{provider}] {status}: {message}")

    @property
    def retryable(self) -> bool:
        return self.status in (408, 429, 500, 502, 503, 504)


class BaseProvider(ABC):
    name: str
    fallback_model: str  # used when failing over to this provider

    @abstractmethod
    async def stream_chat(self, messages: list[ChatMessage], model: str,
                          temperature: float | None):
        """Yield text deltas."""

    @abstractmethod
    async def chat(self, messages: list[ChatMessage], model: str,
                   temperature: float | None) -> str:
        """Return full text."""
