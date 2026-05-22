from __future__ import annotations

from dataclasses import dataclass

from .ollama_client import OllamaClient

DEFAULT_FAST_MODEL = "qwen2.5:3b"
DEFAULT_LARGE_MODEL = "qwen2.5:7b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"


@dataclass(slots=True)
class OllamaRouter:
    """Routes LLM work to fast (JD) and large (company research) Ollama clients."""

    fast: OllamaClient
    large: OllamaClient

    @classmethod
    def from_settings(
        cls,
        *,
        fast_model: str = DEFAULT_FAST_MODEL,
        large_model: str = DEFAULT_LARGE_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
        timeout_seconds: int = 120,
    ) -> OllamaRouter:
        base = base_url.rstrip("/")
        return cls(
            fast=OllamaClient(
                model=fast_model,
                base_url=base,
                timeout_seconds=timeout_seconds,
            ),
            large=OllamaClient(
                model=large_model,
                base_url=base,
                timeout_seconds=timeout_seconds,
            ),
        )
