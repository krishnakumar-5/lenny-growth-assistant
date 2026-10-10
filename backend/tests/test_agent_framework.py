import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.agent.claude_agent_adapter import ClaudeAgentSDKAdapter
from app.services.agent.pi_agent_adapter import (
    PiAgentExecutionError,
    PiAgentTimeoutError,
    PiAgentUnavailableError,
    PiCodingAgentAdapter,
)


@pytest.mark.unit
def test_pi_agent_adapter_generates_ollama_config(tmp_path):
    """Verify that PiCodingAgentAdapter correctly generates models.json for local Ollama."""
    adapter = PiCodingAgentAdapter(
        ollama_base_url="http://localhost:11434",
        ollama_model="llama3:8b",
        config_dir=tmp_path,
    )
    assert adapter.framework_name == "pi_coding_agent"

    config = adapter.generate_ollama_config()
    assert "providers" in config
    assert "ollama" in config["providers"]
    ollama_cfg = config["providers"]["ollama"]
    assert ollama_cfg["baseUrl"] == "http://localhost:11434/v1"
    assert ollama_cfg["api"] == "openai-completions"
    assert ollama_cfg["models"] == [{"id": "llama3:8b"}]

    # Test file writing
    written_path = adapter.write_config_file()
    assert written_path.exists()
    assert written_path.name == "models.json"


@pytest.mark.unit
def test_pi_agent_adapter_availability_detection():
    """Verify Pi adapter reports unavailable with helpful message when CLI is missing."""
    adapter = PiCodingAgentAdapter()
    with patch("shutil.which", return_value=None):
        ok, msg = adapter.check_availability()
        assert ok is False
        assert "npm install -g --ignore-scripts @earendil-works/pi-coding-agent" in msg


@pytest.mark.unit
@pytest.mark.anyio
async def test_pi_agent_execute_query_success(tmp_path):
    """Verify successful subprocess execution and output parsing in print mode."""
    adapter = PiCodingAgentAdapter(
        cli_path="/usr/local/bin/pi",
        config_dir=tmp_path,
        timeout_seconds=10.0,
    )

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(
        return_value=(b"Elena Verna recommends measuring cohort retention weekly.", b"")
    )

    with patch.object(adapter, "find_executable", return_value="/usr/local/bin/pi"):
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc

            response = await adapter.execute_query(prompt="Explain retention")
            assert response == "Elena Verna recommends measuring cohort retention weekly."
            assert mock_exec.called
            # Verify command arguments passed to CLI
            called_args = mock_exec.call_args[0]
            assert called_args[0] == "/usr/local/bin/pi"
            assert called_args[1] == "-p"
            assert "Explain retention" in called_args[2]


@pytest.mark.unit
@pytest.mark.anyio
async def test_pi_agent_execute_query_timeout(tmp_path):
    """Verify PiAgentTimeoutError is raised when CLI execution exceeds timeout."""
    adapter = PiCodingAgentAdapter(
        cli_path="/usr/local/bin/pi",
        config_dir=tmp_path,
        timeout_seconds=0.1,
    )

    mock_proc = MagicMock()
    mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
    mock_proc.kill = MagicMock()
    mock_proc.wait = AsyncMock()

    with patch.object(adapter, "find_executable", return_value="/usr/local/bin/pi"):
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc

            with pytest.raises(PiAgentTimeoutError) as exc_info:
                await adapter.execute_query(prompt="Long query")
            assert "timed out" in str(exc_info.value)
            assert mock_proc.kill.called


@pytest.mark.unit
@pytest.mark.anyio
async def test_pi_agent_execute_query_nonzero_exit(tmp_path):
    """Verify PiAgentExecutionError is raised when CLI exits with non-zero code."""
    adapter = PiCodingAgentAdapter(
        cli_path="/usr/local/bin/pi",
        config_dir=tmp_path,
    )

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.communicate = AsyncMock(
        return_value=(b"", b"Error: Connection to Ollama failed at http://localhost:11434/v1")
    )

    with patch.object(adapter, "find_executable", return_value="/usr/local/bin/pi"):
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc

            with pytest.raises(PiAgentExecutionError) as exc_info:
                await adapter.execute_query(prompt="Query")
            assert "exited with code 1" in str(exc_info.value)
            assert "Connection to Ollama failed" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.anyio
async def test_pi_agent_execute_query_empty_output(tmp_path):
    """Verify PiAgentExecutionError is raised when CLI returns empty stdout."""
    adapter = PiCodingAgentAdapter(
        cli_path="/usr/local/bin/pi",
        config_dir=tmp_path,
    )

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"   \n  \t  ", b""))

    with patch.object(adapter, "find_executable", return_value="/usr/local/bin/pi"):
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc

            with pytest.raises(PiAgentExecutionError) as exc_info:
                await adapter.execute_query(prompt="Query")
            assert "empty response" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.anyio
async def test_pi_agent_execute_query_missing_cli():
    """Verify PiAgentUnavailableError is raised when CLI is not found."""
    adapter = PiCodingAgentAdapter()
    with patch.object(adapter, "find_executable", return_value=None):
        with pytest.raises(PiAgentUnavailableError) as exc_info:
            await adapter.execute_query(prompt="Query")
        assert "not installed or available on PATH" in str(exc_info.value)


@pytest.mark.unit
def test_claude_agent_sdk_adapter_ollama_incompatibility():
    """Verify that ClaudeAgentSDKAdapter explicitly reports incompatibility with Ollama."""
    adapter = ClaudeAgentSDKAdapter(model_name="claude-3-5-sonnet-20241022")
    assert adapter.framework_name == "anthropic_claude_agent_sdk"

    ok, msg = adapter.check_availability(provider_name="ollama")
    assert ok is False
    assert "does not support local Ollama" in msg


@pytest.mark.unit
def test_claude_agent_sdk_adapter_missing_package():
    """Verify ClaudeAgentSDKAdapter reports missing package when not installed."""
    adapter = ClaudeAgentSDKAdapter(model_name="claude-3-5-sonnet-20241022")
    with patch("app.services.agent.claude_agent_adapter.HAS_CLAUDE_AGENT_SDK", False):
        ok, msg = adapter.check_availability(provider_name="anthropic")
        assert ok is False
        assert "pip install claude-agent-sdk" in msg
