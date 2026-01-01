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
        "key_prefix": "sk-",
        "models": [
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "Fast, affordable small model"},
            {"id": "gpt-5-nano", "name": "GPT-5 Nano", "description": "Fastest, most cost-efficient GPT-5"},
            {"id": "gpt-5-mini", "name": "GPT-5 Mini", "description": "Cost-efficient GPT-5 for defined tasks"},
            {"id": "gpt-5", "name": "GPT-5", "description": "Intelligent reasoning model for complex tasks"},
            {"id": "gpt-5.1", "name": "GPT-5.1", "description": "Best for coding and agentic tasks"},
            {"id": "gpt-5.2", "name": "GPT-5.2", "description": "Latest and most capable model"},
            {"id": "gpt-4.1-nano", "name": "GPT-4.1 Nano", "description": "Fastest, most cost-efficient GPT-4.1"},
            {"id": "gpt-4.1-mini", "name": "GPT-4.1 Mini", "description": "Smaller, faster GPT-4.1"},
            {"id": "gpt-4.1", "name": "GPT-4.1", "description": "Smartest non-reasoning model"},
            {"id": "gpt-4o", "name": "GPT-4o", "description": "Fast, intelligent, flexible GPT model"},
        ],
    },
    LLMProvider.ANTHROPIC: {
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-haiku-4-5-latest",
        "key_prefix": "sk-ant-",
        "models": [
            {"id": "claude-haiku-4-5-latest", "name": "Claude Haiku 4.5", "description": "Fast with thinking, 90% of Sonnet performance"},
            {"id": "claude-sonnet-4-5-latest", "name": "Claude Sonnet 4.5", "description": "Best balance with extended thinking"},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "description": "Legacy fast model"},
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "description": "Legacy balanced model"},
        ],
    },
    LLMProvider.GOOGLE: {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-2.5-flash",
        "key_prefix": "",
        "models": [
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "description": "Fast with thinking capabilities"},
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "description": "Previous generation flash"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "description": "Legacy fast model"},
        ],
    },
    LLMProvider.OHMYGPT: {
        "base_url": "https://api.ohmygpt.com/v1",
        "default_model": "gpt-4o-mini",
        "key_prefix": "",
        "models": [
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "OpenAI GPT-4o Mini via OHMYGPT"},
            {"id": "gpt-4o", "name": "GPT-4o", "description": "OpenAI GPT-4o via OHMYGPT"},
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "description": "Anthropic Claude via OHMYGPT"},
        ],
    },
    LLMProvider.OPENROUTER: {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "xiaomi/mimo-v2-flash:free",
        "key_prefix": "sk-or-",
        "models": [
            {"id": "xiaomi/mimo-v2-flash:free", "name": "MiMo-V2-Flash (Free)", "description": "Free - Xiaomi 309B MoE, #1 open-source"},
            {"id": "mistralai/devstral-2512:free", "name": "Devstral 2 (Free)", "description": "Free - Mistral 123B for agentic coding"},
            {"id": "kwaipilot/kat-coder-pro:free", "name": "KAT-Coder-Pro (Free)", "description": "Free - KwaiKAT agentic coding model"},
            {"id": "deepseek/deepseek-r1-0528:free", "name": "DeepSeek R1 (Free)", "description": "Free - DeepSeek 671B reasoning model"},
            {"id": "qwen/qwen3-coder:free", "name": "Qwen3 Coder 480B (Free)", "description": "Free - Qwen 480B for coding tasks"},
            {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B (Free)", "description": "Free - Meta Llama 3.3 multilingual"},
            {"id": "google/gemma-3-27b-it:free", "name": "Gemma 3 27B (Free)", "description": "Free - Google multimodal model"},
            {"id": "openai/gpt-oss-120b:free", "name": "GPT-OSS-120B (Free)", "description": "Free - OpenAI open-source 117B MoE"},
            {"id": "moonshotai/kimi-k2:free", "name": "Kimi K2 (Free)", "description": "Free - Moonshot 1T params, tool use"},
            {"id": "google/gemini-2.0-flash-exp:free", "name": "Gemini 2.0 Flash (Free)", "description": "Free - Google 1M context experimental"},
        ],
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
            "key_prefix": config.get("key_prefix", ""),
            "models": config["models"],
        }
        for provider, config in PROVIDER_CONFIG.items()
    }
