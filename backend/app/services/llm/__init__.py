from typing import Optional

from app.core.config import get_settings
from app.services.llm.base import (
    BaseLLMClient,
    CloudProviderConfigurationError,
    LLMError,
    LLMGenerationError,
    OllamaModelNotFoundError,
    OllamaUnavailableError,
)
from app.services.llm.ollama_client import OllamaClient
from app.services.llm.anthropic_client import AnthropicClient


def get_llm_client(
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None,
) -> BaseLLMClient:
    """Factory creating an LLM client based on requested or default provider.
    
    Fallback Policy:
    Does NOT silently switch providers when an error occurs.
    The configured or requested provider must be used; if unavailable, a clear error
    is returned to the client so that operational failures are transparent.
    """
    settings = get_settings()
    provider = (provider_name or settings.LLM_PROVIDER).strip().lower()

    if provider == "ollama":
        model = model_name or settings.OLLAMA_MODEL
        return OllamaClient(
            base_url=settings.OLLAMA_BASE_URL,
            model_name=model,
            timeout_seconds=settings.OLLAMA_TIMEOUT_SECONDS,
        )
    elif provider == "anthropic":
        model = model_name or settings.ANTHROPIC_MODEL
        return AnthropicClient(
            api_key=settings.ANTHROPIC_API_KEY,
            model_name=model,
            timeout_seconds=settings.ANTHROPIC_TIMEOUT_SECONDS,
        )
    else:
        raise ValueError(
            f"Unsupported LLM provider '{provider}'. Supported providers are: 'ollama', 'anthropic'."
        )


__all__ = [
    "BaseLLMClient",
    "LLMError",
    "OllamaUnavailableError",
    "OllamaModelNotFoundError",
    "CloudProviderConfigurationError",
    "LLMGenerationError",
    "OllamaClient",
    "AnthropicClient",
    "get_llm_client",
]
