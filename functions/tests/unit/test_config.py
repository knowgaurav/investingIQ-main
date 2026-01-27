"""Tests for config module."""
import pytest
from unittest.mock import patch

from shared.config import get_settings, Settings


class TestGetSettings:
    """Tests for get_settings function."""

    def test_loads_from_environment(self):
        """Test settings loads values from environment variables."""
        env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost/testdb",
            "OPENAI_API_KEY": "sk-test-key",
            "OPENAI_BASE_URL": "https://test.api.com/v1",
            "LLM_MODEL": "gpt-4",
            "BACKEND_CALLBACK_URL": "http://test:8000",
            "AZURE_SERVICEBUS_CONNECTION_STRING": "Endpoint=sb://test",
            "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https",
            "ALPHA_VANTAGE_API_KEY": "test-av-key",
        }
        
        # Clear the lru_cache
        get_settings.cache_clear()
        
        with patch.dict("os.environ", env_vars, clear=True):
            settings = get_settings()
        
        assert settings.database_url == "postgresql://test:test@localhost/testdb"
        assert settings.openai_api_key == "sk-test-key"
        assert settings.openai_base_url == "https://test.api.com/v1"
        assert settings.llm_model == "gpt-4"
        assert settings.backend_callback_url == "http://test:8000"
        assert settings.servicebus_connection == "Endpoint=sb://test"
        assert settings.storage_connection == "DefaultEndpointsProtocol=https"
        assert settings.alpha_vantage_api_key == "test-av-key"

    def test_default_values(self):
        """Test default values when env vars not set."""
        # Clear the lru_cache
        get_settings.cache_clear()
        
        with patch.dict("os.environ", {}, clear=True):
            settings = get_settings()
        
        assert settings.database_url == "postgresql://postgres:postgres@localhost:5432/investingiq"
        assert settings.openai_api_key == ""
        assert settings.openai_base_url == "https://ai.megallm.io/v1"
        assert settings.llm_model == "deepseek-ai/deepseek-v3.1"
        assert settings.backend_callback_url == "http://localhost:8000"
        assert settings.servicebus_connection == ""
        assert settings.storage_connection == "UseDevelopmentStorage=true"
        assert settings.alpha_vantage_api_key == ""
