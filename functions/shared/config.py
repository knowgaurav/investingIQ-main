"""Configuration for Azure Functions."""
import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Azure Functions settings loaded from environment variables."""
    
    # Database
    database_url: str
    
    # LLM
    openai_api_key: str
    openai_base_url: str
    llm_model: str
    
    # Backend callback URL for SSE updates
    backend_callback_url: str
    
    # Service Bus
    servicebus_connection: str
    
    # Azure Storage
    storage_connection: str


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings(
        database_url=os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/investingiq"),
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        openai_base_url=os.environ.get("OPENAI_BASE_URL", "https://ai.megallm.io/v1"),
        llm_model=os.environ.get("LLM_MODEL", "deepseek-ai/deepseek-v3.1"),
        backend_callback_url=os.environ.get("BACKEND_CALLBACK_URL", "http://localhost:8000"),
        servicebus_connection=os.environ.get("AZURE_SERVICEBUS_CONNECTION_STRING", ""),
        storage_connection=os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "UseDevelopmentStorage=true"),
    )
