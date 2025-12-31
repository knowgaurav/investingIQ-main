"""Factory pattern for creating LLM provider instances."""
from typing import Optional
from .llm_providers import (
    BaseLLMProvider,
    OpenAIProvider,
    AnthropicProvider,
    GoogleProvider,
    OpenRouterProvider,
    MegaLLMProvider,
    AgentRouterProvider,
)


class LLMProviderFactory:
    """Factory for creating LLM provider instances based on configuration."""
    
    _providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "openrouter": OpenRouterProvider,
        "megallm": MegaLLMProvider,
        "agentrouter": AgentRouterProvider,
    }
    
    @classmethod
    def create(
        cls, 
        provider: str, 
        api_key: str, 
        model: Optional[str] = None
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider: Provider name (openai, anthropic, google, etc.)
            api_key: User's API key for the provider
            model: Optional model name (uses default if not specified)
            
        Returns:
            Configured LLM provider instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider_lower = provider.lower()
        if provider_lower not in cls._providers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        provider_class = cls._providers[provider_lower]
        return provider_class(api_key=api_key, model=model)
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported provider names."""
        return list(cls._providers.keys())
