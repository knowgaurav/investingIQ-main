"""LLM API key verification endpoint."""
import logging
from fastapi import APIRouter, HTTPException
from openai import OpenAI
import anthropic

from app.models.schemas import LLMVerifyRequest, LLMVerifyResponse, LLMProvider

logger = logging.getLogger(__name__)
router = APIRouter()

PROVIDER_CONFIG = {
    LLMProvider.OPENAI: {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-5-mini", "gpt-5-nano"],
    },
    LLMProvider.ANTHROPIC: {
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-haiku-4-5-latest",
        "models": ["claude-haiku-4-5-latest", "claude-sonnet-4-5-latest", "claude-3-5-haiku-latest"],
    },
    LLMProvider.GOOGLE: {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-2.5-flash",
        "models": ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"],
    },
    LLMProvider.OPENROUTER: {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "openai/gpt-4o-mini",
        "models": ["openai/gpt-4o-mini", "anthropic/claude-3.5-haiku", "google/gemini-2.0-flash-exp"],
    },
    LLMProvider.MEGALLM: {
        "base_url": "https://api.megallm.com/v1",
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o-mini", "claude-haiku", "gemini-flash"],
    },
    LLMProvider.AGENTROUTER: {
        "base_url": "https://api.agentrouter.ai/v1",
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o-mini", "claude-haiku", "gemini-flash"],
    },
}


def get_provider_config(provider: LLMProvider) -> dict:
    """Get configuration for a provider."""
    return PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG[LLMProvider.OPENAI])


@router.post("/llm/verify", response_model=LLMVerifyResponse)
async def verify_llm_key(request: LLMVerifyRequest) -> LLMVerifyResponse:
    """Verify an LLM API key by making a minimal test request."""
    config = get_provider_config(request.provider)
    model = request.model or config["default_model"]
    
    try:
        if request.provider == LLMProvider.ANTHROPIC:
            return await _verify_anthropic(request.api_key, model)
        else:
            return await _verify_openai_compatible(
                request.api_key, 
                config["base_url"], 
                model
            )
    except Exception as e:
        logger.error(f"LLM verification failed for {request.provider}: {e}")
        return LLMVerifyResponse(valid=False, error=str(e))


async def _verify_openai_compatible(api_key: str, base_url: str, model: str) -> LLMVerifyResponse:
    """Verify OpenAI-compatible API key."""
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1,
        )
        return LLMVerifyResponse(valid=True)
    except Exception as e:
        error_msg = str(e)
        if "invalid_api_key" in error_msg.lower() or "unauthorized" in error_msg.lower():
            return LLMVerifyResponse(valid=False, error="Invalid API key")
        if "model" in error_msg.lower() and "not found" in error_msg.lower():
            return LLMVerifyResponse(valid=False, error=f"Model '{model}' not available")
        return LLMVerifyResponse(valid=False, error=error_msg[:200])


async def _verify_anthropic(api_key: str, model: str) -> LLMVerifyResponse:
    """Verify Anthropic API key."""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        client.messages.create(
            model=model,
            max_tokens=1,
            messages=[{"role": "user", "content": "Hi"}],
        )
        return LLMVerifyResponse(valid=True)
    except anthropic.AuthenticationError:
        return LLMVerifyResponse(valid=False, error="Invalid API key")
    except anthropic.NotFoundError:
        return LLMVerifyResponse(valid=False, error=f"Model '{model}' not available")
    except Exception as e:
        return LLMVerifyResponse(valid=False, error=str(e)[:200])


@router.get("/llm/providers")
async def get_providers():
    """Get available LLM providers and their models."""
    return {
        provider.value: {
            "default_model": config["default_model"],
            "models": config["models"],
        }
        for provider, config in PROVIDER_CONFIG.items()
    }
