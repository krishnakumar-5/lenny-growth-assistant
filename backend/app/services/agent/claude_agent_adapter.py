import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import claude_agent_sdk
    HAS_CLAUDE_AGENT_SDK = True
except ImportError:
    claude_agent_sdk = None
    HAS_CLAUDE_AGENT_SDK = False


class ClaudeAgentSDKAdapter:
    """Adapter interfacing with the Anthropic Claude Agent SDK (claude-agent-sdk).
    
    Architecture Note & Limitation:
    The Claude Agent SDK is designed exclusively for Anthropic's Claude infrastructure
    wrapping the compiled Claude Code CLI binary. It DOES NOT support local LLM backends
    like Ollama. Consequently, in environments executing local Ollama demos, the agent
    execution path must utilize an Ollama-compatible tool harness while reserving the
    Claude Agent SDK for cloud Anthropic execution.
    """

    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022") -> None:
        self.model_name = model_name

    @property
    def framework_name(self) -> str:
        return "anthropic_claude_agent_sdk"

    def is_sdk_installed(self) -> bool:
        """Check whether the claude-agent-sdk package is installed in the current environment."""
        return HAS_CLAUDE_AGENT_SDK

    def check_availability(self, provider_name: str = "anthropic") -> Tuple[bool, str]:
        """Verify SDK availability and provider compatibility."""
        if provider_name == "ollama":
            return (
                False,
                "The Anthropic Claude Agent SDK does not support local Ollama models. "
                "The Claude Agent SDK is hardcoded to Anthropic's Claude Code infrastructure. "
                "For Ollama execution, use the Ollama Tool Agent harness or the Pi Coding Agent.",
            )

        if not self.is_sdk_installed():
            return (
                False,
                "The 'claude-agent-sdk' package is not installed in the environment. "
                "Install it using 'pip install claude-agent-sdk' (requires Python 3.10+).",
            )

        return True, f"Claude Agent SDK is available for model '{self.model_name}'."
