"""PLAYBOOK Python SDK — Runtime safety for AI agents.

Usage:
    import playbook_sdk

    playbook_sdk.init(endpoint="https://playbook.internal", api_key="your-key")

    @playbook_sdk.guard(agent_id="agent-001")
    def my_agent_action(tool, params):
        return tool.execute(params)
"""

from .client import PlaybookClient
from .config import SDKConfig
from .exceptions import (
    GuardBlockedError,
    GuardError,
    GuardQuarantinedError,
    PlaybookError,
)
from .guard import Guard, guard
from .heartbeat import HeartbeatSender

__version__ = "0.1.0"

# Global SDK state
_global_client: PlaybookClient | None = None


def init(endpoint: str | None = None, api_key: str | None = None) -> None:
    """Initialize the global PLAYBOOK client."""
    global _global_client
    _global_client = PlaybookClient(endpoint=endpoint, api_key=api_key)


def get_client() -> PlaybookClient:
    """Get the global PLAYBOOK client."""
    if _global_client is None:
        raise RuntimeError(
            "PLAYBOOK SDK not initialized. Call playbook_sdk.init() first."
        )
    return _global_client


__all__ = [
    "PlaybookClient",
    "SDKConfig",
    "Guard",
    "guard",
    "HeartbeatSender",
    "PlaybookError",
    "GuardError",
    "GuardBlockedError",
    "GuardQuarantinedError",
    "init",
    "get_client",
    "__version__",
    # Middleware (lazy-imported)
    "PlaybookCallbackHandler",
    "crewai_guard",
    "CrewAIGuard",
]
