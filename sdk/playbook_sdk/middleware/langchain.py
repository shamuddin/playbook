"""LangChain middleware integration for PLAYBOOK SDK.

Provides a LangChain callback handler that intercepts tool and LLM calls
and evaluates them through the PLAYBOOK Judge Layer before execution.

Usage:
    from playbook_sdk.middleware.langchain import PlaybookCallbackHandler

    handler = PlaybookCallbackHandler(agent_id="langchain-agent-001")

    llm = OpenAI(callbacks=[handler])
    tools = [tool1, tool2]
    agent = initialize_agent(tools, llm, callbacks=[handler])
"""

import asyncio
import logging
from typing import Any, Callable, Optional

from playbook_sdk.client import PlaybookClient
from playbook_sdk.exceptions import GuardBlockedError, GuardQuarantinedError

logger = logging.getLogger("playbook.middleware.langchain")

try:
    from langchain.callbacks.base import BaseCallbackHandler
except ImportError:  # pragma: no cover
    BaseCallbackHandler = None  # type: ignore[misc,assignment]


if BaseCallbackHandler is None:

    class _Placeholder:
        """Placeholder raised when langchain is not installed."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError(
                "LangChain integration requires 'langchain' to be installed. "
                "Install it with: pip install playbook-guard[langchain]"
            )

    PlaybookCallbackHandler = _Placeholder  # type: ignore[misc,assignment]
else:

    class PlaybookCallbackHandler(BaseCallbackHandler):  # type: ignore[no-redef]
        """LangChain callback handler that judges tool and LLM calls.

        Intercepts ``on_tool_start`` and ``on_llm_start`` events, sends
        action metadata to the PLAYBOOK Judge Layer, and enforces the
        verdict (ALLOW / BLOCK / QUARANTINE / ESCALATE).

        Parameters
        ----------
        agent_id:
            Identifier for the agent making the calls.
        endpoint:
            PLAYBOOK API base URL.
        api_key:
            PLAYBOOK API key.
        on_block:
            Optional callback invoked when a call is BLOCKED.
        on_quarantine:
            Optional callback invoked when a call is QUARANTINED.
        action_types:
            Mapping of event type → ``action_type`` sent to the Judge.
            Defaults judge tool calls as ``langchain_tool_call`` and
            LLM calls as ``langchain_llm_call``.
        """

        def __init__(
            self,
            agent_id: Optional[str] = None,
            endpoint: Optional[str] = None,
            api_key: Optional[str] = None,
            on_block: Optional[Callable] = None,
            on_quarantine: Optional[Callable] = None,
            action_types: Optional[dict[str, str]] = None,
        ) -> None:
            self.agent_id = agent_id or "langchain-agent"
            self.on_block = on_block
            self.on_quarantine = on_quarantine
            self.client = PlaybookClient(endpoint=endpoint, api_key=api_key)
            self.action_types = action_types or {
                "tool": "langchain_tool_call",
                "llm": "langchain_llm_call",
            }

        def _run_judge(
            self,
            action_type: str,
            action_details: dict[str, Any],
        ) -> dict[str, Any]:
            """Run the async ``judge()`` call from a sync context."""
            try:
                return asyncio.run(
                    self.client.judge(
                        agent_id=self.agent_id,
                        action_type=action_type,
                        action_details=action_details,
                    )
                )
            except RuntimeError as exc:
                # If we're already inside an async event loop (e.g. Jupyter
                # or an async LangChain chain), asyncio.run() is forbidden.
                # In those environments users should apply ``@guard`` to
                # individual tools instead of using this callback handler.
                logger.warning(
                    "Cannot run judge inside an existing event loop (%s). "
                    "Use @guard on individual tools for async LangChain chains.",
                    exc,
                )
                # Fail-open: let the action proceed
                return {"verdict": "ESCALATE", "reason": "Event-loop conflict"}
            except Exception as exc:
                logger.warning("Judge evaluation failed: %s", exc)
                return {"verdict": "ESCALATE", "reason": str(exc)}

        def _handle_verdict(
            self,
            verdict: dict[str, Any],
            action_name: str,
            *cb_args: Any,
            **cb_kwargs: Any,
        ) -> None:
            """Enforce the Judge verdict."""
            decision = verdict.get("verdict", "ESCALATE")

            if decision == "ALLOW":
                return

            if decision == "BLOCK":
                if self.on_block:
                    self.on_block(verdict, *cb_args, **cb_kwargs)
                    return
                raise GuardBlockedError(
                    f"LangChain action '{action_name}' blocked by PLAYBOOK: "
                    f"{verdict.get('reason', 'No reason')}"
                )

            if decision == "QUARANTINE":
                if self.on_quarantine:
                    self.on_quarantine(verdict, *cb_args, **cb_kwargs)
                    return
                raise GuardQuarantinedError(
                    f"LangChain action '{action_name}' quarantined by PLAYBOOK: "
                    f"{verdict.get('reason', 'No reason')}"
                )

            # ESCALATE / HUMAN_REVIEW
            logger.warning(
                "Judge returned %s for %s: %s",
                decision,
                action_name,
                verdict.get("reason", "No reason"),
            )

        # ------------------------------------------------------------------
        # LangChain callback hooks
        # ------------------------------------------------------------------

        def on_tool_start(
            self,
            serialized: dict[str, Any],
            input_str: str,
            **kwargs: Any,
        ) -> None:
            """Intercept a tool call before execution."""
            tool_name = serialized.get("name", "unknown") if isinstance(serialized, dict) else "unknown"
            action_details = {
                "tool": tool_name,
                "input": input_str,
                "framework": "langchain",
            }
            verdict = self._run_judge(
                self.action_types["tool"],
                action_details,
            )
            self._handle_verdict(verdict, tool_name)

        def on_llm_start(
            self,
            serialized: dict[str, Any],
            prompts: list[str],
            **kwargs: Any,
        ) -> None:
            """Intercept an LLM call before execution."""
            model_name = "unknown"
            if isinstance(serialized, dict):
                model_name = serialized.get("name") or serialized.get("id", ["unknown"])[-1]

            action_details = {
                "model": model_name,
                "prompt_count": len(prompts),
                "prompt_preview": prompts[0][:200] if prompts else "",
                "framework": "langchain",
            }
            verdict = self._run_judge(
                self.action_types["llm"],
                action_details,
            )
            self._handle_verdict(verdict, f"llm:{model_name}")

        async def close(self) -> None:
            """Close the underlying HTTP client."""
            await self.client.close()
