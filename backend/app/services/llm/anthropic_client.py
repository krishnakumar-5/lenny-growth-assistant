import logging
from typing import Dict, List, Optional, Tuple
import anthropic

from app.services.llm.base import (
    BaseLLMClient,
    CloudProviderConfigurationError,
    LLMGenerationError,
)

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """Cloud LLM client interfacing with Anthropic Claude models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "claude-3-5-sonnet-20241022",
        timeout_seconds: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def timeout_seconds(self) -> float:
        return self._timeout_seconds

    async def check_availability(self) -> Tuple[bool, str]:
        """Verify that Anthropic API key is configured."""
        if not self._api_key or not self._api_key.strip():
            return (
                False,
                "Anthropic API key is not configured. Set the ANTHROPIC_API_KEY environment variable.",
            )
        return (
            True,
            f"Anthropic client configured with model '{self._model_name}'.",
        )

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Call Anthropic Messages API to generate grounded text."""
        if not self._api_key or not self._api_key.strip():
            raise CloudProviderConfigurationError(
                "Anthropic API key is not configured. Set ANTHROPIC_API_KEY in your environment."
            )

        client = anthropic.AsyncAnthropic(
            api_key=self._api_key,
            timeout=self._timeout_seconds,
        )

        formatted_messages: List[Dict[str, str]] = []
        for msg in messages:
            role = msg.get("role", "user")
            # Anthropic messages API only accepts 'user' and 'assistant' roles
            if role in ("user", "assistant"):
                formatted_messages.append(
                    {"role": role, "content": msg.get("content", "")}
                )

        if not formatted_messages:
            raise LLMGenerationError("No user or assistant messages provided to Anthropic client.")

        try:
            kwargs = {
                "model": self._model_name,
                "messages": formatted_messages,
                "max_tokens": 1500,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await client.messages.create(**kwargs)

            text_parts = [
                block.text
                for block in response.content
                if getattr(block, "type", "") == "text" and hasattr(block, "text")
            ]
            full_text = "".join(text_parts).strip()
            if not full_text:
                raise LLMGenerationError("Anthropic API returned an empty text content.")
            return full_text

        except anthropic.AuthenticationError as e:
            logger.error("Anthropic authentication failed: %s", e)
            raise CloudProviderConfigurationError(
                "Invalid or unauthorized Anthropic API key."
            ) from e
        except anthropic.RateLimitError as e:
            logger.error("Anthropic rate limit reached: %s", e)
            raise LLMGenerationError(
                "Anthropic rate limit reached. Please retry in a few moments."
            ) from e
        except anthropic.APITimeoutError as e:
            logger.error("Anthropic request timed out: %s", e)
            raise LLMGenerationError(
                f"Anthropic API request timed out after {self._timeout_seconds} seconds."
            ) from e
        except anthropic.APIError as e:
            logger.error("Anthropic API error: %s", e)
            raise LLMGenerationError(
                f"Anthropic API request failed with status {getattr(e, 'status_code', 'unknown')}."
            ) from e
        except Exception as e:
            logger.error("Unexpected error in Anthropic client: %s", e)
            raise LLMGenerationError(
                "An unexpected error occurred while communicating with Anthropic Claude."
            ) from e
