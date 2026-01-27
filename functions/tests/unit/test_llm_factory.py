"""Tests for LLM factory module."""
import pytest
from unittest.mock import patch, MagicMock

from shared.llm_factory import LLMProviderFactory
from shared.llm_providers import (
    OpenAIProvider,
    AnthropicProvider,
    GoogleProvider,
    OpenRouterProvider,
    OHMYGPTProvider,
)


class TestLLMProviderFactory:
    """Tests for LLMProviderFactory."""

    @patch('shared.llm_providers.ChatOpenAI')
    def test_create_openai(self, mock_chat):
        """Test creating OpenAI provider."""
        provider = LLMProviderFactory.create("openai", "test-key")
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "test-key"

    @patch('langchain_anthropic.ChatAnthropic')
    def test_create_anthropic(self, mock_chat):
        """Test creating Anthropic provider."""
        provider = LLMProviderFactory.create("anthropic", "test-key")
        assert isinstance(provider, AnthropicProvider)
        assert provider.api_key == "test-key"

    @patch('shared.llm_providers.ChatOpenAI')
    def test_create_google(self, mock_chat):
        """Test creating Google provider."""
        provider = LLMProviderFactory.create("google", "test-key")
        assert isinstance(provider, GoogleProvider)
        assert provider.api_key == "test-key"

    @patch('shared.llm_providers.ChatOpenAI')
    def test_create_openrouter(self, mock_chat):
        """Test creating OpenRouter provider."""
        provider = LLMProviderFactory.create("openrouter", "test-key")
        assert isinstance(provider, OpenRouterProvider)
        assert provider.api_key == "test-key"

    @patch('shared.llm_providers.ChatOpenAI')
    def test_create_ohmygpt(self, mock_chat):
        """Test creating OHMYGPT provider."""
        provider = LLMProviderFactory.create("ohmygpt", "test-key")
        assert isinstance(provider, OHMYGPTProvider)
        assert provider.api_key == "test-key"

    @patch('shared.llm_providers.ChatOpenAI')
    def test_create_case_insensitive(self, mock_chat):
        """Test provider name is case insensitive."""
        provider = LLMProviderFactory.create("OPENAI", "test-key")
        assert isinstance(provider, OpenAIProvider)

    def test_invalid_provider_raises(self):
        """Test invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMProviderFactory.create("invalid_provider", "test-key")

    def test_get_supported_providers(self):
        """Test get_supported_providers returns all providers."""
        providers = LLMProviderFactory.get_supported_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" in providers
        assert "openrouter" in providers
        assert "ohmygpt" in providers
        assert len(providers) == 5

    @patch('shared.llm_providers.ChatOpenAI')
    def test_create_with_custom_model(self, mock_chat):
        """Test creating provider with custom model."""
        provider = LLMProviderFactory.create("openai", "test-key", model="gpt-4")
        assert provider.model == "gpt-4"


# Property-Based Tests
from hypothesis import given, strategies as st, settings


class TestLLMFactoryProviderCreationProperty:
    """Property-based tests for LLM factory provider creation.
    
    **Feature: functions-testing-setup, Property 4: LLM Factory Provider Creation**
    **Validates: Requirements 6.4**
    """

    @settings(max_examples=100)
    @given(provider_name=st.sampled_from(LLMProviderFactory.get_supported_providers()))
    @patch('langchain_anthropic.ChatAnthropic')
    @patch('shared.llm_providers.ChatOpenAI')
    def test_supported_provider_returns_instance(self, mock_openai, mock_anthropic, provider_name):
        """For any supported provider name, create() SHALL return an instance of the corresponding provider class."""
        provider_classes = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "google": GoogleProvider,
            "openrouter": OpenRouterProvider,
            "ohmygpt": OHMYGPTProvider,
        }
        
        provider = LLMProviderFactory.create(provider_name, "test-api-key")
        expected_class = provider_classes[provider_name]
        
        assert isinstance(provider, expected_class)
        assert provider.api_key == "test-api-key"
