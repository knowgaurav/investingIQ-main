"""Factory for creating LLM provider strategy instances.

This module implements the Factory pattern for creating provider instances
using dependency injection. It supports OpenAI, Anthropic, Google, OHMYGPT,
and OpenRouter providers.
"""

from collections.abc import Callable

from .llm_providers_v2 import (
    AnthropicStrategy,
    GoogleStrategy,
    LLMProviderStrategy,
    OpenAICompatibleStrategy,
)


class LLMProviderFactory:
    """Factory for creating provider strategy instances using dependency injection."""

    PROVIDERS: dict[str, Callable[[], LLMProviderStrategy]] = {
        "openai": lambda: OpenAICompatibleStrategy(
            provider_id="openai",
            base_url="https://api.openai.com/v1/chat/completions",
            key_prefix="sk-"
        ),
        "anthropic": lambda: AnthropicStrategy(),
        "google": lambda: GoogleStrategy(),
        "ohmygpt": lambda: OpenAICompatibleStrategy(
            provider_id="ohmygpt",
            base_url="https://api.ohmygpt.com/v1/chat/completions",
            key_prefix=""
        ),
        "openrouter": lambda: OpenAICompatibleStrategy(
            provider_id="openrouter",
            base_url="https://openrouter.ai/api/v1/chat/completions",
            key_prefix="sk-or-"
        ),
    }

    @classmethod
    def get_provider(cls, provider_id: str) -> LLMProviderStrategy:
        """Get provider strategy by ID."""
        if provider_id not in cls.PROVIDERS:
            supported = ", ".join(cls.PROVIDERS.keys())
            raise ValueError(f"Unknown provider: {provider_id}. Supported: {supported}")
        return cls.PROVIDERS[provider_id]()

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider IDs."""
        return list(cls.PROVIDERS.keys())

    @classmethod
    def is_openai_compatible(cls, provider_id: str) -> bool:
        """Check if provider uses OpenAI-compatible API format."""
        openai_compatible = {"openai", "ohmygpt", "openrouter"}
        return provider_id in openai_compatible
