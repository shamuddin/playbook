"""SDK configuration helpers."""

import os
from typing import Optional


class SDKConfig:
    """Configuration for the PLAYBOOK SDK."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 5.0,
        heartbeat_interval: float = 60.0,
    ):
        self.endpoint = endpoint or os.environ.get(
            "PLAYBOOK_ENDPOINT", "http://localhost:8000"
        )
        self.api_key = api_key or os.environ.get("PLAYBOOK_API_KEY", "")
        self.timeout = timeout
        self.heartbeat_interval = heartbeat_interval

    @classmethod
    def from_env(cls) -> "SDKConfig":
        """Load configuration from environment variables."""
        return cls(
            endpoint=os.environ.get("PLAYBOOK_ENDPOINT"),
            api_key=os.environ.get("PLAYBOOK_API_KEY"),
            timeout=float(os.environ.get("PLAYBOOK_TIMEOUT", "5.0")),
            heartbeat_interval=float(
                os.environ.get("PLAYBOOK_HEARTBEAT_INTERVAL", "60.0")
            ),
        )
