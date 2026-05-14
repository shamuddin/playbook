"""Guard decorator for agent actions."""

import asyncio
import functools
import logging
from typing import Any, Callable, Optional

from .client import PlaybookClient
from .exceptions import GuardBlockedError, GuardQuarantinedError

logger = logging.getLogger("playbook.guard")


class Guard:
    """Guard decorator for agent actions."""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        on_block: Optional[Callable] = None,
        on_quarantine: Optional[Callable] = None,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.agent_id = agent_id or "default"
        self.action_type = action_type or "tool_call"
        self.on_block = on_block
        self.on_quarantine = on_quarantine
        self.client = PlaybookClient(endpoint=endpoint, api_key=api_key)

    async def evaluate(self, func_name: str, args: tuple, kwargs: dict) -> dict:
        """Send action to Judge Layer for evaluation."""
        action_details = {
            "function": func_name,
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys()),
            "action_summary": f"{func_name}({', '.join(repr(a)[:100] for a in args)})",
        }
        result = await self.client.judge(
            agent_id=self.agent_id,
            action_type=self.action_type,
            action_details=action_details,
        )
        return result

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            verdict = await self.evaluate(func.__name__, args, kwargs)
            decision = verdict.get("verdict", "ESCALATE")

            if decision == "ALLOW":
                return await func(*args, **kwargs)

            elif decision == "BLOCK":
                if self.on_block:
                    return await self.on_block(verdict, *args, **kwargs)
                raise GuardBlockedError(
                    f"Action '{func.__name__}' blocked by PLAYBOOK: {verdict.get('reason', 'No reason')}"
                )

            elif decision == "QUARANTINE":
                if self.on_quarantine:
                    return await self.on_quarantine(verdict, *args, **kwargs)
                raise GuardQuarantinedError(
                    f"Action '{func.__name__}' quarantined by PLAYBOOK: {verdict.get('reason', 'No reason')}"
                )

            else:
                # ESCALATE or HUMAN_REVIEW — proceed but log
                logger.warning(
                    "Judge returned %s for %s: %s",
                    decision,
                    func.__name__,
                    verdict.get("reason", "No reason"),
                )
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            import asyncio

            verdict = asyncio.run(self.evaluate(func.__name__, args, kwargs))
            decision = verdict.get("verdict", "ESCALATE")

            if decision == "ALLOW":
                return func(*args, **kwargs)

            elif decision == "BLOCK":
                if self.on_block:
                    return self.on_block(verdict, *args, **kwargs)
                raise GuardBlockedError(
                    f"Action '{func.__name__}' blocked by PLAYBOOK: {verdict.get('reason', 'No reason')}"
                )

            elif decision == "QUARANTINE":
                if self.on_quarantine:
                    return self.on_quarantine(verdict, *args, **kwargs)
                raise GuardQuarantinedError(
                    f"Action '{func.__name__}' quarantined by PLAYBOOK: {verdict.get('reason', 'No reason')}"
                )

            else:
                logger.warning(
                    "Judge returned %s for %s: %s",
                    decision,
                    func.__name__,
                    verdict.get("reason", "No reason"),
                )
                return func(*args, **kwargs)

        # Return async wrapper if func is a coroutine function, else sync wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper


def guard(
    agent_id: Optional[str] = None,
    action_type: Optional[str] = None,
    on_block: Optional[Callable] = None,
    on_quarantine: Optional[Callable] = None,
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Guard:
    """Factory to create a Guard decorator."""
    return Guard(
        agent_id=agent_id,
        action_type=action_type,
        on_block=on_block,
        on_quarantine=on_quarantine,
        endpoint=endpoint,
        api_key=api_key,
    )
