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
        "default_model": "gpt-5.4-mini",
        "key_prefix": "sk-",
        "models": [
            {"id": "gpt-5.4-mini", "name": "GPT-5.4 Mini", "description": "Strongest mini model for coding and subagents"},
            {"id": "gpt-5.4-nano", "name": "GPT-5.4 Nano", "description": "Cheapest GPT-5.4-class for high-volume tasks"},
            {"id": "gpt-5.4", "name": "GPT-5.4", "description": "Affordable model for coding and professional work"},
            {"id": "gpt-5.5", "name": "GPT-5.5", "description": "Frontier intelligence for coding and professional work"},
            {"id": "gpt-5.5-pro", "name": "GPT-5.5 Pro", "description": "Smarter, more precise responses for complex tasks"},
        ],
    },
    LLMProvider.ANTHROPIC: {
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-haiku-4-5",
        "key_prefix": "sk-ant-",
        "models": [
            {"id": "claude-haiku-4-5", "name": "Claude Haiku 4.5", "description": "Fastest model with near-frontier intelligence"},
            {"id": "claude-sonnet-4-5", "name": "Claude Sonnet 4.5", "description": "Previous balance of speed and intelligence"},
            {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "description": "Best balance of speed and intelligence"},
            {"id": "claude-opus-4-7", "name": "Claude Opus 4.7", "description": "Capable model for complex agentic coding"},
            {"id": "claude-opus-4-8", "name": "Claude Opus 4.8", "description": "Most capable model for reasoning and agentic coding"},
        ],
    },
    LLMProvider.GOOGLE: {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-3.1-flash-lite",
        "key_prefix": "",
        "models": [
            {"id": "gemini-3.1-flash-lite", "name": "Gemini 3.1 Flash-Lite", "description": "Frontier-class performance at lowest cost"},
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "description": "Advanced reasoning with 1M context"},
            {"id": "gemini-3-flash-preview", "name": "Gemini 3 Flash", "description": "Frontier performance rivaling larger models"},
            {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash", "description": "Most intelligent for agentic and coding tasks"},
            {"id": "gemini-3.1-pro-preview", "name": "Gemini 3.1 Pro", "description": "Most advanced intelligence and agentic coding"},
        ],
    },
    LLMProvider.OHMYGPT: {
        "base_url": "https://api.ohmygpt.com/v1",
        "default_model": "gpt-5.4-mini",
        "key_prefix": "",
        "models": [
            {"id": "gpt-5.4-mini", "name": "GPT-5.4 Mini", "description": "OpenAI GPT-5.4 Mini via OHMYGPT"},
            {"id": "gpt-5.5", "name": "GPT-5.5", "description": "OpenAI frontier model via OHMYGPT"},
            {"id": "claude-haiku-4-5", "name": "Claude Haiku 4.5", "description": "Anthropic Haiku via OHMYGPT"},
            {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "description": "Anthropic Sonnet via OHMYGPT"},
            {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash", "description": "Google Gemini via OHMYGPT"},
        ],
    },
    LLMProvider.OPENROUTER: {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "moonshotai/kimi-k2.6:free",
        "key_prefix": "sk-or-",
        "models": [
            {"id": "moonshotai/kimi-k2.6:free", "name": "Kimi K2.6 (Free)", "description": "Free - Moonshot multimodal, long-horizon coding"},
            {"id": "deepseek/deepseek-v4-flash:free", "name": "DeepSeek V4 Flash (Free)", "description": "Free - DeepSeek 284B MoE, 1M context"},
            {"id": "qwen/qwen3-coder:free", "name": "Qwen3 Coder 480B (Free)", "description": "Free - Qwen 480B for coding tasks"},
            {"id": "qwen/qwen3-next-80b-a3b-instruct:free", "name": "Qwen3 Next 80B (Free)", "description": "Free - Qwen 80B for reasoning and code"},
            {"id": "minimax/minimax-m2.5:free", "name": "MiniMax M2.5 (Free)", "description": "Free - SOTA model for coding and agents"},
            {"id": "z-ai/glm-4.5-air:free", "name": "GLM 4.5 Air (Free)", "description": "Free - Z.ai agent-centric MoE model"},
            {"id": "nvidia/nemotron-3-super-120b-a12b:free", "name": "Nemotron 3 Super 120B (Free)", "description": "Free - NVIDIA 120B MoE for multi-agent"},
            {"id": "openai/gpt-oss-120b:free", "name": "GPT-OSS-120B (Free)", "description": "Free - OpenAI open-source 117B MoE"},
            {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B (Free)", "description": "Free - Meta Llama 3.3 multilingual"},
            {"id": "google/gemma-4-31b-it:free", "name": "Gemma 4 31B (Free)", "description": "Free - Google multimodal model"},
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
