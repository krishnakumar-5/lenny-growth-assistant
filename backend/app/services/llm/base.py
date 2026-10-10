from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


class LLMError(Exception):
    """Base exception for LLM provider errors."""
    pass


class OllamaUnavailableError(LLMError):
    """Raised when the local Ollama service cannot be reached."""
    pass


class OllamaModelNotFoundError(LLMError):
    """Raised when the specified model is not installed/pulled in Ollama."""
    pass


class CloudProviderConfigurationError(LLMError):
    """Raised when a cloud provider is missing credentials or misconfigured."""
    pass


class LLMGenerationError(LLMError):
    """Raised when LLM text generation encounters an upstream failure."""
    pass


class BaseLLMClient(ABC):
    """Abstract interface for LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'ollama', 'anthropic')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Configured model identifier."""
        pass

    @property
    @abstractmethod
    def timeout_seconds(self) -> float:
        """Configured timeout in seconds."""
        pass

    @abstractmethod
    async def check_availability(self) -> Tuple[bool, str]:
        """Verify provider availability and model presence without generating text."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate response text for the provided conversation messages."""
        pass
