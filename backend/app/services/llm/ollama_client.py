import logging
from typing import Dict, List, Optional, Tuple
import httpx

from app.services.llm.base import (
    BaseLLMClient,
    LLMGenerationError,
    OllamaModelNotFoundError,
    OllamaUnavailableError,
)

logger = logging.getLogger(__name__)


class OllamaClient(BaseLLMClient):
    """Asynchronous Ollama client communicating with the local Ollama daemon."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "qwen2.5:3b",
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def timeout_seconds(self) -> float:
        return self._timeout_seconds

    @property
    def base_url(self) -> str:
        return self._base_url

    async def check_availability(self) -> Tuple[bool, str]:
        """Verify reachability of the Ollama server and check if the requested model exists."""
        tags_url = f"{self._base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                res = await client.get(tags_url)
                if res.status_code != 200:
                    return (
                        False,
                        f"Ollama server returned status {res.status_code} when querying models.",
                    )
                data = res.json()
                models = [
                    m.get("name", "")
                    for m in data.get("models", [])
                    if isinstance(m, dict)
                ]

                # Check exact match or prefix/tag match (e.g. 'llama3:8b' vs 'llama3:8b-instruct')
                target = self._model_name.lower()
                target_base = target.split(":")[0]
                model_exists = any(
                    target == m.lower()
                    or m.lower().startswith(f"{target}:")
                    or (":" not in target and m.lower().split(":")[0] == target_base)
                    for m in models
                )

                if not model_exists:
                    return (
                        False,
                        f"Model '{self._model_name}' is not installed in Ollama. "
                        f"Available models: {models or 'none'}. Pull it with 'ollama pull {self._model_name}'.",
                    )

                return True, f"Ollama service reachable and model '{self._model_name}' is available."

        except httpx.ConnectError:
            return (
                False,
                f"Ollama service is unreachable at {self._base_url}. "
                "Please verify that the Ollama service is running ('ollama serve').",
            )
        except httpx.TimeoutException:
            return (
                False,
                f"Connection to Ollama timed out after {self._timeout_seconds} seconds.",
            )
        except Exception as e:
            logger.warning("Unexpected error checking Ollama availability: %s", e)
            return False, f"Failed to connect to Ollama service: {str(e)}"

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Call Ollama chat API to generate a response."""
        chat_url = f"{self._base_url}/api/chat"

        formatted_messages: List[Dict[str, str]] = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            formatted_messages.append(
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            )

        payload = {
            "model": self._model_name,
            "messages": formatted_messages,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                res = await client.post(chat_url, json=payload)

                if res.status_code == 404:
                    raise OllamaModelNotFoundError(
                        f"Model '{self._model_name}' was not found by Ollama server."
                    )

                res.raise_for_status()
                data = res.json()
                message_obj = data.get("message", {})
                content = message_obj.get("content", "")
                if not content:
                    raise LLMGenerationError(
                        "Ollama returned an empty response content."
                    )
                return content

        except httpx.ConnectError as e:
            logger.error("Connection error communicating with Ollama: %s", e)
            raise OllamaUnavailableError(
                f"Could not connect to Ollama service at {self._base_url}. "
                "Please ensure the Ollama daemon is running."
            ) from e
        except httpx.TimeoutException as e:
            logger.error("Timeout waiting for Ollama response: %s", e)
            raise LLMGenerationError(
                f"Ollama response generation timed out after {self._timeout_seconds} seconds."
            ) from e
        except OllamaModelNotFoundError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error("Ollama HTTP status error %s: %s", e.response.status_code, e)
            raise LLMGenerationError(
                f"Ollama request failed with HTTP status {e.response.status_code}."
            ) from e
        except Exception as e:
            logger.error("Unexpected error during Ollama generation: %s", e)
            raise LLMGenerationError(
                "An unexpected error occurred while communicating with the local LLM."
            ) from e
