"""Client interface for OpenAI-style APIs (stubbed for offline use)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


class OpenAIClientError(RuntimeError):
    """Raised when an OpenAI client operation fails."""


@dataclass
class OpenAIClient:
    """Minimal wrapper around an OpenAI-compatible API."""

    api_key: Optional[str] = None
    base_url: str = "https://api.openai.com/v1"

    def __post_init__(self) -> None:
        if not self.api_key:
            raise OpenAIClientError("API key is required for OpenAI client usage.")

    def generate(self, model: str, prompt: str, **kwargs: Dict[str, str]) -> str:
        """Proxy a completion request to an external API."""

        raise OpenAIClientError("Network access is disabled in this environment.")
