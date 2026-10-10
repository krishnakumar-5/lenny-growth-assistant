from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest

from app.services.llm.base import (
    CloudProviderConfigurationError,
    LLMGenerationError,
    OllamaModelNotFoundError,
    OllamaUnavailableError,
)
from app.services.llm.ollama_client import OllamaClient
from app.services.llm.anthropic_client import AnthropicClient
from app.services.llm import get_llm_client


# ============================================================================
# Ollama Client Unit Tests
# ============================================================================


@pytest.mark.unit
def test_ollama_client_initialization():
    """Verify OllamaClient properties and default configuration."""
    client_default = OllamaClient()
    assert client_default.model_name == "qwen2.5:3b"

    client = OllamaClient(
        base_url="http://localhost:11434/",
        model_name="qwen2.5:3b",
        timeout_seconds=25.0,
    )
    assert client.provider_name == "ollama"
    assert client.model_name == "qwen2.5:3b"
    assert client.timeout_seconds == 25.0
    assert client.base_url == "http://localhost:11434"


@pytest.mark.unit
@pytest.mark.anyio
async def test_ollama_check_availability_model_present():
    """Verify check_availability succeeds when model is returned by /api/tags."""
    client = OllamaClient(base_url="http://localhost:11434", model_name="llama3:8b")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "llama3:8b"}, {"name": "mistral:7b"}]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        ok, msg = await client.check_availability()
        assert ok is True
        assert "reachable" in msg
        assert "llama3:8b" in msg


@pytest.mark.unit
@pytest.mark.anyio
async def test_ollama_check_availability_model_missing():
    """Verify check_availability reports missing model when not present in tags."""
    client = OllamaClient(base_url="http://localhost:11434", model_name="llama3:8b")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "mistral:7b"}]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        ok, msg = await client.check_availability()
        assert ok is False
        assert "not installed" in msg


@pytest.mark.unit
@pytest.mark.anyio
async def test_ollama_check_availability_server_down():
    """Verify check_availability handles connection failure gracefully."""
    client = OllamaClient(base_url="http://localhost:11434", model_name="llama3:8b")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        ok, msg = await client.check_availability()
        assert ok is False
        assert "unreachable" in msg


@pytest.mark.unit
@pytest.mark.anyio
async def test_ollama_generate_response_success():
    """Verify successful response text generation via Ollama chat API."""
    client = OllamaClient(base_url="http://localhost:11434", model_name="llama3:8b")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {"role": "assistant", "content": "Retention is determined by cohort engagement."}
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await client.generate_response(
            messages=[{"role": "user", "content": "What is retention?"}],
            system_prompt="You are a growth advisor.",
        )
        assert result == "Retention is determined by cohort engagement."
        assert mock_post.called
        called_payload = mock_post.call_args[1]["json"]
        assert called_payload["model"] == "llama3:8b"
        assert called_payload["messages"][0]["role"] == "system"


@pytest.mark.unit
@pytest.mark.anyio
async def test_ollama_generate_response_connect_error():
    """Verify OllamaUnavailableError raised when connection fails during generation."""
    client = OllamaClient(base_url="http://localhost:11434", model_name="llama3:8b")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Cannot connect")
        with pytest.raises(OllamaUnavailableError):
            await client.generate_response(messages=[{"role": "user", "content": "hi"}])


@pytest.mark.unit
@pytest.mark.anyio
async def test_ollama_generate_response_timeout():
    """Verify LLMGenerationError raised when Ollama times out."""
    client = OllamaClient(base_url="http://localhost:11434", model_name="llama3:8b")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        with pytest.raises(LLMGenerationError) as exc_info:
            await client.generate_response(messages=[{"role": "user", "content": "hi"}])
        assert "timed out" in str(exc_info.value)


# ============================================================================
# Anthropic Client Unit Tests
# ============================================================================


@pytest.mark.unit
@pytest.mark.anyio
async def test_anthropic_check_availability_missing_key():
    """Verify Anthropic reports unavailable when API key is absent."""
    client = AnthropicClient(api_key=None)
    ok, msg = await client.check_availability()
    assert ok is False
    assert "not configured" in msg


@pytest.mark.unit
@pytest.mark.anyio
async def test_anthropic_check_availability_with_key():
    """Verify Anthropic reports available when API key is provided."""
    client = AnthropicClient(api_key="sk-ant-test-key-12345")
    ok, msg = await client.check_availability()
    assert ok is True
    assert "claude-3-5-sonnet" in msg


@pytest.mark.unit
@pytest.mark.anyio
async def test_anthropic_generate_response_missing_key_raises():
    """Verify CloudProviderConfigurationError when attempting to generate without key."""
    client = AnthropicClient(api_key=None)
    with pytest.raises(CloudProviderConfigurationError):
        await client.generate_response(messages=[{"role": "user", "content": "hello"}])


@pytest.mark.unit
@pytest.mark.anyio
async def test_anthropic_generate_response_success():
    """Verify Anthropic response extraction using mocked AsyncAnthropic."""
    client = AnthropicClient(api_key="sk-ant-mocked-key")

    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "Growth loops compound user acquisitions."

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    with patch("anthropic.AsyncAnthropic") as mock_cls:
        instance = mock_cls.return_value
        instance.messages.create = AsyncMock(return_value=mock_response)

        result = await client.generate_response(
            messages=[{"role": "user", "content": "Explain growth loops"}],
            system_prompt="Growth system prompt",
        )
        assert result == "Growth loops compound user acquisitions."


# ============================================================================
# Factory Unit Tests
# ============================================================================


@pytest.mark.unit
def test_get_llm_client_factory_ollama():
    """Verify factory returns OllamaClient for 'ollama' with default model 'qwen2.5:3b'."""
    client = get_llm_client(provider_name="ollama")
    assert isinstance(client, OllamaClient)
    assert client.provider_name == "ollama"
    assert client.model_name == "qwen2.5:3b"

    # Verify custom model override works
    client_custom = get_llm_client(provider_name="ollama", model_name="mistral:7b")
    assert client_custom.model_name == "mistral:7b"


@pytest.mark.unit
def test_get_llm_client_factory_anthropic():
    """Verify factory returns AnthropicClient for 'anthropic'."""
    client = get_llm_client(provider_name="anthropic", model_name="claude-3-haiku-20240307")
    assert isinstance(client, AnthropicClient)
    assert client.provider_name == "anthropic"
    assert client.model_name == "claude-3-haiku-20240307"


@pytest.mark.unit
def test_get_llm_client_factory_invalid_provider():
    """Verify factory raises ValueError for unknown provider."""
    with pytest.raises(ValueError) as exc:
        get_llm_client(provider_name="unsupported_provider")
    assert "Unsupported LLM provider" in str(exc.value)
