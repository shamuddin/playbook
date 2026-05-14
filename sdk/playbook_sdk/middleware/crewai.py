"""CrewAI middleware integration for PLAYBOOK SDK.

Provides a ``@crewai_guard`` decorator that wraps CrewAI task functions
and evaluates them through the PLAYBOOK Judge Layer before execution.

Usage:
    from playbook_sdk.middleware.crewai import crewai_guard

    @crewai_guard(agent_id="researcher-001")
    @task
    def research_task(agent):
        ...
"""

import asyncio
import functools
import logging
from typing import Any, Callable, Optional

from playbook_sdk.client import PlaybookClient
from playbook_sdk.exceptions import GuardBlockedError, GuardQuarantinedError

logger = logging.getLogger("playbook.middleware.crewai")


class CrewAIGuard:
    """Guard decorator tailored for CrewAI tasks.

    Works identically to the core ``Guard`` class but adds automatic
    ``agent_id`` extraction from CrewAI ``Agent`` objects when available.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        on_block: Optional[Callable] = None,
        on_quarantine: Optional[Callable] = None,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self.agent_id = agent_id or "crewai-agent"
        self.action_type = action_type or "crewai_task"
        self.on_block = on_block
        self.on_quarantine = on_quarantine
        self.client = PlaybookClient(endpoint=endpoint, api_key=api_key)

    def _resolve_agent_id(self, args: tuple[Any, ...]) -> str:
        """Try to extract a more specific agent_id from a CrewAI Agent object."""
        if not args:
            return self.agent_id
        first_arg = args[0]
        # CrewAI Agent objects have a ``role`` attribute
        if hasattr(first_arg, "role"):
            role = getattr(first_arg, "role")
            if isinstance(role, str) and role:
                return role
        return self.agent_id

    async def evaluate(self, func_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        """Send action to Judge Layer for evaluation."""
        resolved_id = self._resolve_agent_id(args)
        action_details = {
            "function": func_name,
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys()),
            "action_summary": f"{func_name}({', '.join(repr(a)[:100] for a in args)})",
            "framework": "crewai",
        }
        try:
            result = await self.client.judge(
                agent_id=resolved_id,
                action_type=self.action_type,
                action_details=action_details,
            )
            return result
        except Exception as exc:
            logger.warning("Judge evaluation failed for %s: %s", func_name, exc)
            # Fail-open: let the action proceed
            return {"verdict": "ESCALATE", "reason": str(exc)}

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            verdict = await self.evaluate(func.__name__, args, kwargs)
            decision = verdict.get("verdict", "ESCALATE")

            if decision == "ALLOW":
                return await func(*args, **kwargs)

            if decision == "BLOCK":
                if self.on_block:
                    return await self.on_block(verdict, *args, **kwargs)
                raise GuardBlockedError(
                    f"CrewAI task '{func.__name__}' blocked by PLAYBOOK: "
                    f"{verdict.get('reason', 'No reason')}"
                )

            if decision == "QUARANTINE":
                if self.on_quarantine:
                    return await self.on_quarantine(verdict, *args, **kwargs)
                raise GuardQuarantinedError(
                    f"CrewAI task '{func.__name__}' quarantined by PLAYBOOK: "
                    f"{verdict.get('reason', 'No reason')}"
                )

            logger.warning(
                "Judge returned %s for %s: %s",
                decision,
                func.__name__,
                verdict.get("reason", "No reason"),
            )
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            verdict = asyncio.run(self.evaluate(func.__name__, args, kwargs))
            decision = verdict.get("verdict", "ESCALATE")

            if decision == "ALLOW":
                return func(*args, **kwargs)

            if decision == "BLOCK":
                if self.on_block:
                    return self.on_block(verdict, *args, **kwargs)
                raise GuardBlockedError(
                    f"CrewAI task '{func.__name__}' blocked by PLAYBOOK: "
                    f"{verdict.get('reason', 'No reason')}"
                )

            if decision == "QUARANTINE":
                if self.on_quarantine:
                    return self.on_quarantine(verdict, *args, **kwargs)
                raise GuardQuarantinedError(
                    f"CrewAI task '{func.__name__}' quarantined by PLAYBOOK: "
                    f"{verdict.get('reason', 'No reason')}"
                )

            logger.warning(
                "Judge returned %s for %s: %s",
                decision,
                func.__name__,
                verdict.get("reason", "No reason"),
            )
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper


    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.close()


def crewai_guard(
    agent_id: Optional[str] = None,
    action_type: Optional[str] = None,
    on_block: Optional[Callable] = None,
    on_quarantine: Optional[Callable] = None,
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
) -> CrewAIGuard:
    """Factory to create a CrewAI-specific Guard decorator."""
    return CrewAIGuard(
        agent_id=agent_id,
        action_type=action_type,
        on_block=on_block,
        on_quarantine=on_quarantine,
        endpoint=endpoint,
        api_key=api_key,
    )
