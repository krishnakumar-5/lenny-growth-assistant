import asyncio
import json
import logging
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class PiAgentException(Exception):
    """Base exception for Pi Coding Agent execution errors."""
    pass


class PiAgentUnavailableError(PiAgentException):
    """Raised when the Pi CLI executable is not installed or reachable."""
    pass


class PiAgentTimeoutError(PiAgentException):
    """Raised when Pi CLI execution exceeds the configured timeout."""
    pass


class PiAgentExecutionError(PiAgentException):
    """Raised when Pi CLI returns a non-zero exit code or malformed output."""
    pass


class PiCodingAgentAdapter:
    """Production runtime adapter executing the official Pi Coding Agent CLI.
    
    Authoritative Package: @earendil-works/pi-coding-agent (npm)
    Executable: pi (or pi.cmd on Windows)
    Interface: Print mode (`pi -p <prompt>`) or RPC mode (`pi --mode rpc`)
    Model Bridge: Uses ~/.pi/agent/models.json to connect to local Ollama via
                  the OpenAI-compatible /v1 endpoint (http://localhost:11434/v1).
    """

    def __init__(
        self,
        cli_path: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
        ollama_model: Optional[str] = None,
        config_dir: Optional[Path] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        settings = get_settings()
        self.cli_path = cli_path or settings.PI_CLI_PATH
        self.ollama_base_url = (ollama_base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.ollama_model = ollama_model or settings.OLLAMA_MODEL
        custom_dir = config_dir or (Path(settings.PI_CONFIG_DIR) if settings.PI_CONFIG_DIR else None)
        self.config_dir = custom_dir or (Path.home() / ".pi" / "agent")
        self.timeout_seconds = timeout_seconds or settings.PI_TIMEOUT_SECONDS

    @property
    def framework_name(self) -> str:
        return "pi_coding_agent"

    def find_executable(self) -> Optional[str]:
        """Locate the 'pi' CLI executable on PATH or via explicit configuration."""
        if self.cli_path:
            p = Path(self.cli_path)
            if p.exists() and p.is_file():
                return str(p.resolve())

        # Check standard executable names across platforms
        for candidate in ("pi", "pi.cmd", "pi.exe", "pi.ps1"):
            found = shutil.which(candidate)
            if found:
                return found

        return None

    def is_cli_installed(self) -> bool:
        """Return True if the pi CLI executable is present."""
        return self.find_executable() is not None

    def generate_ollama_config(self) -> Dict[str, Any]:
        """Generate official models.json schema for local Ollama."""
        return {
            "providers": {
                "ollama": {
                    "baseUrl": f"{self.ollama_base_url}/v1",
                    "api": "openai-completions",
                    "apiKey": "ollama",
                    "models": [{"id": self.ollama_model}],
                }
            }
        }

    def write_config_file(self) -> Path:
        """Persist models.json into the Pi agent configuration directory."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        config_path = self.config_dir / "models.json"
        config_data = self.generate_ollama_config()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
        logger.info("Wrote Pi coding agent models configuration to %s", config_path)
        return config_path

    def check_availability(self) -> Tuple[bool, str]:
        """Check if Pi CLI is installed and configured."""
        exe = self.find_executable()
        if not exe:
            return (
                False,
                "Pi Coding Agent executable ('pi') was not found on PATH. "
                "Install it using 'npm install -g --ignore-scripts @earendil-works/pi-coding-agent'.",
            )
        return True, f"Pi Coding Agent executable is available at '{exe}'."

    async def execute_query(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: str = "ollama",
        timeout: Optional[float] = None,
    ) -> str:
        """Spawn the Pi Coding Agent subprocess in print mode and return the response."""
        exe = self.find_executable()
        if not exe:
            raise PiAgentUnavailableError(
                "Pi Coding Agent CLI ('pi') is not installed or available on PATH. "
                "Install it globally via 'npm install -g --ignore-scripts @earendil-works/pi-coding-agent'."
            )

        # Write or ensure models.json exists for the target provider
        try:
            self.write_config_file()
        except Exception as e:
            logger.warning("Could not persist Pi models.json to %s: %s", self.config_dir, e)

        target_model = model or self.ollama_model
        if os.name == "nt" and exe.lower().endswith((".cmd", ".ps1")):
            node_exe = shutil.which("node")
            launcher = Path(exe).with_name("pi-launcher.js")

            if not node_exe or not launcher.is_file():
                raise RuntimeError(
                    "Could not find Node.js or the Pi launcher."
                )

            cmd: List[str] = [
                node_exe,
                str(launcher),
                "--provider", provider,
                "--model", target_model,
                "--print",
                "--no-session",
                prompt,
            ]
        else:
            cmd: List[str] = [
                exe,
                "--provider", provider,
                "--model", target_model,
                "--print",
                "--no-session",
                prompt,
            ]


        effective_timeout = timeout or self.timeout_seconds
        env = dict(os.environ)

        logger.info("Invoking Pi Coding Agent runtime: %s", exe)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=effective_timeout,
                )
            except asyncio.TimeoutError as e:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                raise PiAgentTimeoutError(
                    f"Pi Coding Agent execution timed out after {effective_timeout} seconds."
                ) from e

            if proc.returncode != 0:
                err_text = stderr_data.decode("utf-8", errors="replace").strip()
                logger.error("Pi CLI failed with exit code %s: %s", proc.returncode, err_text)
                raise PiAgentExecutionError(
                    f"Pi Coding Agent exited with code {proc.returncode}: {err_text or 'Unknown runtime error'}"
                )

            output_text = stdout_data.decode("utf-8", errors="replace").strip()
            if not output_text:
                raise PiAgentExecutionError("Pi Coding Agent returned an empty response.")

            return output_text

        except (PiAgentUnavailableError, PiAgentTimeoutError, PiAgentExecutionError):
            raise
        except FileNotFoundError as e:
            raise PiAgentUnavailableError(f"Failed to launch Pi executable '{exe}': file not found.") from e
        except Exception as e:
            logger.error("Unexpected error invoking Pi Coding Agent: %s", e, exc_info=True)
            raise PiAgentExecutionError(
                f"An unexpected failure occurred while executing the Pi Coding Agent: {str(e)}"
            ) from e
