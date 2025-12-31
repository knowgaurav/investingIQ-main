"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    app_name: str = "InvestingIQ"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/investingiq"
    
    # Redis (for local queue)
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # Azure Service Bus
    azure_servicebus_connection_string: str = ""
    
    # LLM (OpenAI-compatible API)
    openai_api_key: str = ""
    openai_base_url: str = "https://ai.megallm.io/v1"
    llm_model: str = "deepseek-ai/deepseek-v3.1"
    
    # News API
    news_api_key: str = ""
    
    # MLflow
    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_experiment_name: str = "investingiq-llm"
    
    # Rate limiting
    rate_limit: str = "100/minute"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
