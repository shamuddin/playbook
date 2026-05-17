"""Agent Simulator Playground engine.

Runs one or more simulated agents that:
1. Pick a random situation
2. Call an LLM to decide the best action
3. Apply the @guard decorator via the Judge Layer
4. Execute or block the action
5. Emit real-time events via WebSocket
"""

from __future__ import annotations

import asyncio
import json
import random
import textwrap
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import INCIDENT_TYPES
from app.database import AsyncSessionLocal
from app.models import (
    Agent,
    JudgeDecision,
    PlaygroundAgent,
    PlaygroundEvent,
    PlaygroundEventType,
    PlaygroundSession,
    PlaygroundSessionStatus,
    utc_now,
)
from app.services.detect.engine import DetectionEngine, DetectionResult
from app.services.detect.incident_factory import IncidentFactory
from app.services.detect.normalizer import normalize_event
from app.services.playground.llm_providers import LLMProviderFactory
from app.services.websocket_manager import ws_manager


@dataclass
class AgentAction:
    name: str
    metadata_template: dict
    is_malicious: bool = False


@dataclass
class SimulatedAgent:
    id: str
    name: str
    role: str
    risk_level: str
    system_prompt: str
    situations: list[str]
    actions: list[AgentAction]
    provider_name: str
    provider_config: dict
    is_active: bool = True

    # Runtime state
    current_metadata: dict = field(default_factory=dict)
    last_thought: str = ""
    last_action: str = ""
    last_verdict: str = ""
    last_verdict_data: dict = field(default_factory=dict)


def _build_llm_prompt(system_prompt: str, situation: str, actions: list[AgentAction]) -> str:
    action_list = [a.name for a in actions]
    return textwrap.dedent(
        f"""\
        {system_prompt}

        CURRENT SITUATION:
        "{situation}"

        AVAILABLE ACTIONS:
        {json.dumps(action_list, indent=2)}

        INSTRUCTIONS:
        Choose the single most appropriate action for the situation above.
        Respond ONLY with a JSON object in this exact format (no markdown, no extra text):
        {{
          "action": "<one of the available actions>",
          "reasoning": "<2-3 sentence professional justification>",
          "confidence": <number between 0.0 and 1.0>
        }}
        """
    )


def _apply_situation_metadata(metadata: dict, situation: str) -> dict:
    """Dynamically tweak metadata based on situation keywords."""
    low = situation.lower()
    if any(k in low for k in ("unauthenticated", "no auth", "token expired", "unauthorized")):
        metadata["auth_present"] = False
    if any(k in low for k in ("admin", "authorized", "manager", "hr")):
        metadata["auth_present"] = True
    if any(k in low for k in ("after hours", "weekend", "night", "evening")):
        metadata["is_business_hours"] = False
    if "business hours" in low:
        metadata["is_business_hours"] = True
    return metadata


async def _call_judge_layer(
    agent_id: str,
    action_type: str,
    action_name: str,
    metadata: dict,
) -> dict:
    """Call the Judge Layer evaluation endpoint directly.

    This mirrors what the SDK @guard decorator does internally.
    """
    from app.routers.judge import evaluate_action
    from app.schemas import JudgeEvaluateRequest
    from app.database import get_db

    async with AsyncSessionLocal() as db:
        try:
            request = JudgeEvaluateRequest(
                action=action_name,
                agent_id=agent_id,
                action_type=action_type,
                metadata=metadata,
            )
            result = await evaluate_action(request=request, db=db)
            return {
                "verdict": result.verdict,
                "rationale": result.rationale,
                "latency_ms": result.latency_ms,
                "severity_score": result.severity_score,
                "confidence": result.confidence,
                "matched_rules": result.matched_rules,
                "bypass_patterns_detected": result.bypass_patterns_detected,
            }
        except Exception as exc:
            return {
                "verdict": "ESCALATE",
                "rationale": f"Judge evaluation failed: {exc}",
                "latency_ms": 0.0,
                "severity_score": 0,
                "confidence": 0.0,
                "matched_rules": [],
                "bypass_patterns_detected": [],
            }


class PlaygroundEngine:
    """Orchestrates one or more simulated agents."""

    def __init__(self, session_id: str, handoff_chain: Optional[list[str]] = None, misbehavior_mode: bool = False):
        self.session_id = session_id
        self.agents: list[SimulatedAgent] = []
        self.running = False
        self._tasks: list[asyncio.Task] = []
        self._stop_event = asyncio.Event()
        self.handoff_chain: list[str] = handoff_chain or []
        self.misbehavior_mode = misbehavior_mode

        # Human-in-the-loop state
        self.awaiting_human_approval: Optional[dict] = None
        self._human_decision_event = asyncio.Event()
        self._human_decision: Optional[str] = None

    async def load_from_db(self, db: AsyncSession) -> None:
        """Load session + agent configs from the database."""
        result = await db.execute(
            select(PlaygroundSession).where(PlaygroundSession.id == self.session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Playground session {self.session_id} not found")

        agent_result = await db.execute(
            select(PlaygroundAgent).where(PlaygroundAgent.session_id == self.session_id)
        )
        db_agents = agent_result.scalars().all()

        for a in db_agents:
            actions = []
            for act in a.actions or []:
                actions.append(
                    AgentAction(
                        name=act.get("name", "unknown"),
                        metadata_template=act.get("metadata", {}),
                        is_malicious=act.get("is_malicious", False),
                    )
                )
            self.agents.append(
                SimulatedAgent(
                    id=a.id,
                    name=a.name,
                    role=a.role,
                    risk_level=a.risk_level,
                    system_prompt=a.system_prompt,
                    situations=a.situations or [],
                    actions=actions,
                    provider_name=session.provider_name,
                    provider_config=session.provider_config,
                    is_active=a.is_active,
                )
            )

        # Mirror playground agents into the main Agent table for health-page visibility
        # Use a scoped system_id so each session gets its own Agent records
        async with AsyncSessionLocal() as agent_db:
            for sim_agent in self.agents:
                scoped_id = f"pg-{self.session_id[:8]}-{sim_agent.name}"
                result = await agent_db.execute(
                    select(Agent).where(Agent.system_id == scoped_id)
                )
                agent_record = result.scalar_one_or_none()
                if agent_record:
                    agent_record.status = "online"
                    # Preserve existing health; only reset for brand-new records
                    if agent_record.health_score is None:
                        agent_record.health_score = 100
                    agent_record.is_active = True
                    agent_record.name = sim_agent.name
                else:
                    agent_record = Agent(
                        system_id=scoped_id,
                        name=sim_agent.name,
                        description=f"Playground agent ({self.session_id[:8]})",
                        status="online",
                        health_score=100,
                        is_active=True,
                    )
                    agent_db.add(agent_record)
            await agent_db.commit()

    async def start(self) -> None:
        """Start the simulation loop for all agents."""
        self.running = True
        self._stop_event.clear()
        await self._emit_event(
            PlaygroundEventType.SYSTEM,
            {"message": "Simulation started", "agent_count": len(self.agents)},
        )

        if self.handoff_chain:
            # Swarm mode: one task runs the handoff chain repeatedly
            task = asyncio.create_task(self._swarm_loop())
            self._tasks.append(task)
        else:
            # Legacy mode: each agent runs independently
            for agent in self.agents:
                if agent.is_active:
                    task = asyncio.create_task(self._agent_loop(agent))
                    self._tasks.append(task)

        for agent in self.agents:
            if agent.is_active:
                await ws_manager.broadcast({
                    "event_type": "agent_status_updated",
                    "agent_id": f"pg-{self.session_id[:8]}-{agent.name}",
                    "system_id": f"pg-{self.session_id[:8]}-{agent.name}",
                    "agent_name": agent.name,
                    "status": "online",
                    "health_score": 100,
                })

    async def stop(self) -> None:
        """Signal all agent loops to stop."""
        self.running = False
        self._stop_event.set()
        for task in self._tasks:
            if not task.done():
                task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        # Mark mirrored Agent records as offline
        async with AsyncSessionLocal() as agent_db:
            for sim_agent in self.agents:
                scoped_id = f"pg-{self.session_id[:8]}-{sim_agent.name}"
                result = await agent_db.execute(
                    select(Agent).where(Agent.system_id == scoped_id)
                )
                agent_record = result.scalar_one_or_none()
                if agent_record:
                    agent_record.status = "offline"
            await agent_db.commit()

        for agent in self.agents:
            await ws_manager.broadcast({
                "event_type": "agent_status_updated",
                "agent_id": f"pg-{self.session_id[:8]}-{agent.name}",
                "system_id": f"pg-{self.session_id[:8]}-{agent.name}",
                "agent_name": agent.name,
                "status": "offline",
                "health_score": 0,
            })

        await self._emit_event(
            PlaygroundEventType.SYSTEM,
            {"message": "Simulation stopped"},
        )

    # ------------------------------------------------------------------
    # Human-in-the-Loop
    # ------------------------------------------------------------------

    async def request_human_approval(self, event_data: dict) -> str:
        """Pause simulation and wait for human approve/deny. Returns 'approve' or 'deny'."""
        self.awaiting_human_approval = event_data
        await self._emit_event(
            PlaygroundEventType.HUMAN_APPROVAL_REQUESTED,
            {"requires_approval": True, **event_data}
        )
        await self._human_decision_event.wait()
        return self._human_decision or "deny"

    def submit_human_decision(self, decision: str) -> None:
        self._human_decision = decision
        self._human_decision_event.set()
        self.awaiting_human_approval = None
        self._human_decision_event = asyncio.Event()

    def _requires_human_approval(self, agent: SimulatedAgent, action_name: str, verdict: dict) -> bool:
        """Request human approval when Judge returns QUARANTINE or when confidence is low."""
        if verdict.get("verdict") == "QUARANTINE":
            return True
        if agent.risk_level == "critical" and verdict.get("severity_score", 0) > 70:
            return True
        return False

    # ------------------------------------------------------------------
    # Swarm / Handoff
    # ------------------------------------------------------------------

    async def _swarm_loop(self) -> None:
        """Continuously execute swarm_ticks until stopped."""
        while self.running and not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=random.uniform(4, 10))
                break  # stop_event was set
            except asyncio.TimeoutError:
                pass

            if not self.running:
                break

            await self.swarm_tick()

    async def swarm_tick(self) -> None:
        """One pass through the handoff chain.

        If Agent A's action was ALLOWED, pass its output as the "situation"
        for Agent B. If BLOCKED/QUARANTINED, stop the chain and notify
        ComplianceBot.
        """
        situation: Optional[str] = None
        for agent_name in self.handoff_chain:
            if not self.running or self._stop_event.is_set():
                break

            agent = next((a for a in self.agents if a.name == agent_name), None)
            if not agent or not agent.is_active:
                continue

            result = await self._run_agent_tick(agent, situation=situation)

            await self._emit_event(
                PlaygroundEventType.HANDOFF,
                {
                    "from_agent": agent.name,
                    "verdict": result["verdict"],
                    "action": result["action_name"],
                },
                agent_id=agent.id,
                agent_name=agent.name,
            )

            if result["verdict"] in ("DENY", "BLOCK", "QUARANTINE"):
                await self._emit_event(
                    PlaygroundEventType.SYSTEM,
                    {
                        "message": (
                            f"Chain stopped at {agent.name} due to {result['verdict']}. "
                            "ComplianceBot notified."
                        ),
                        "stopped_agent": agent.name,
                        "verdict": result["verdict"],
                    },
                    agent_id=agent.id,
                    agent_name=agent.name,
                )
                break

            # Pass output as situation for the next agent in chain
            situation = (
                f"Previous agent '{agent.name}' performed '{result['action_name']}' "
                f"with reasoning: {result['reasoning'][:200]}"
            )

    # ------------------------------------------------------------------
    # Legacy single-agent loop
    # ------------------------------------------------------------------

    async def _agent_loop(self, agent: SimulatedAgent) -> None:
        """Main lifecycle for a single simulated agent (legacy mode)."""
        await self._emit_event(
            PlaygroundEventType.SYSTEM,
            {"message": f"Agent {agent.name} is online", "agent_name": agent.name, "role": agent.role},
            agent_id=agent.id,
            agent_name=agent.name,
        )

        while self.running and not self._stop_event.is_set():
            # Random tick interval: 4–10 seconds (fast enough for demo, slow enough to read)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=random.uniform(4, 10))
                break  # stop_event was set
            except asyncio.TimeoutError:
                pass

            if not self.running:
                break

            if not agent.situations:
                continue

            situation = random.choice(agent.situations)
            await self._run_agent_tick(agent, situation=situation)

        await self._emit_event(
            PlaygroundEventType.SYSTEM,
            {"message": f"Agent {agent.name} shut down"},
            agent_id=agent.id,
            agent_name=agent.name,
        )

    # ------------------------------------------------------------------
    # Shared tick logic
    # ------------------------------------------------------------------

    async def _run_agent_tick(
        self, agent: SimulatedAgent, situation: Optional[str] = None
    ) -> dict:
        """Execute one full think-act-judge cycle for an agent.

        Returns a dict with keys: verdict, action_name, reasoning, situation, is_malicious.
        """
        provider = LLMProviderFactory.create(agent.provider_name, agent.provider_config)

        # If no explicit situation provided, pick a random one
        if situation is None:
            situation = random.choice(agent.situations) if agent.situations else "No situation"

        # 1) Agent thinks about situation
        await self._emit_event(
            PlaygroundEventType.AGENT_THOUGHT,
            {"situation": situation, "agent_role": agent.role},
            agent_id=agent.id,
            agent_name=agent.name,
        )

        # 2) Call LLM for decision — unless misbehavior mode forces a malicious action
        action_name = ""
        reasoning = ""
        confidence = 0.5
        llm_resp = None

        malicious_actions = [a for a in agent.actions if a.is_malicious]
        if self.misbehavior_mode and malicious_actions and random.random() < 0.70:
            # Force malicious action for demo realism
            chosen = random.choice(malicious_actions)
            action_name = chosen.name
            reasoning = (
                f"[MISBEHAVIOR] Agent {agent.name} deliberately chose '{action_name}' "
                f"despite policy constraints. Simulated insider threat / compromised-agent scenario."
            )
            confidence = 0.92
            await self._emit_event(
                PlaygroundEventType.LLM_RESPONSE,
                {
                    "reasoning": reasoning,
                    "confidence": confidence,
                    "chosen_action": action_name,
                    "provider": "chaos_mode",
                    "model": "misbehavior_injected",
                    "latency_ms": 0.0,
                },
                agent_id=agent.id,
                agent_name=agent.name,
            )
        else:
            prompt = _build_llm_prompt(agent.system_prompt, situation, agent.actions)
            llm_resp = await provider.chat_completion(
                system_prompt=agent.system_prompt,
                messages=[{"role": "user", "content": situation}],
                json_mode=True,
                temperature=0.7,
            )

            if llm_resp.error:
                await self._emit_event(
                    PlaygroundEventType.ERROR,
                    {"error": llm_resp.error, "provider": llm_resp.provider},
                    agent_id=agent.id,
                    agent_name=agent.name,
                )
                # Fallback: pick random action
                action_name = random.choice([a.name for a in agent.actions]) if agent.actions else "noop"
                reasoning = f"[FALLBACK] LLM error: {llm_resp.error}. Defaulting to {action_name}."
                confidence = 0.0
            else:
                structured = llm_resp.structured or {}
                action_name = structured.get("action", "")
                reasoning = structured.get("reasoning", "No reasoning provided.")
                confidence = float(structured.get("confidence", 0.5))

                # Validate action exists
                valid_names = {a.name for a in agent.actions}
                if action_name not in valid_names:
                    choices = [a.name for a in agent.actions]
                    print(f"[DEBUG] choices={choices} random={random.choice(choices) if choices else 'noop'}")
                    fallback = random.choice(choices) if choices else "noop"
                    await self._emit_event(
                        PlaygroundEventType.ERROR,
                        {"error": f"LLM chose unknown action '{action_name}', falling back to {fallback}"},
                        agent_id=agent.id,
                        agent_name=agent.name,
                    )
                    action_name = fallback

                agent.last_thought = reasoning
                await self._emit_event(
                    PlaygroundEventType.LLM_RESPONSE,
                    {
                        "reasoning": reasoning,
                        "confidence": confidence,
                        "chosen_action": action_name,
                        "provider": llm_resp.provider,
                        "model": llm_resp.model,
                        "latency_ms": round(llm_resp.latency_ms, 2),
                    },
                    agent_id=agent.id,
                    agent_name=agent.name,
                )

        # 3) Build metadata for guard
        action_obj = next((a for a in agent.actions if a.name == action_name), None)
        if action_obj:
            meta = dict(action_obj.metadata_template)
            meta = _apply_situation_metadata(meta, situation)
            meta["declared_intent"] = action_name
            meta["llm_confidence"] = confidence
            meta["situation"] = situation[:200]
            agent.current_metadata = meta
        else:
            agent.current_metadata = {}

        # 4) Emit action requested
        await self._emit_event(
            PlaygroundEventType.ACTION_REQUESTED,
            {
                "action": action_name,
                "metadata": agent.current_metadata,
                "is_malicious": action_obj.is_malicious if action_obj else False,
            },
            agent_id=agent.id,
            agent_name=agent.name,
        )

        # 5) Call Judge Layer
        print(f"[DEBUG] {agent.name} action={action_name} meta={agent.current_metadata}")
        verdict = await _call_judge_layer(
            agent_id=agent.name,
            action_type=agent.role,
            action_name=action_name,
            metadata=agent.current_metadata,
        )
        agent.last_verdict = verdict.get("verdict", "ESCALATE")
        agent.last_verdict_data = verdict

        await self._emit_event(
            PlaygroundEventType.JUDGE_VERDICT,
            {
                "verdict": verdict.get("verdict"),
                "rationale": verdict.get("rationale"),
                "latency_ms": verdict.get("latency_ms"),
                "severity_score": verdict.get("severity_score"),
                "confidence": verdict.get("confidence"),
                "matched_rules": verdict.get("matched_rules", []),
                "bypass_patterns": verdict.get("bypass_patterns_detected", []),
            },
            agent_id=agent.id,
            agent_name=agent.name,
        )

        # 6) Human-in-the-loop approval check
        if self._requires_human_approval(agent, action_name, verdict):
            human_decision = await self.request_human_approval(
                {
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "action": action_name,
                    "verdict": verdict.get("verdict"),
                    "rationale": verdict.get("rationale"),
                    "severity_score": verdict.get("severity_score"),
                }
            )
            if human_decision == "deny":
                agent.last_verdict = "DENY"
                await self._emit_event(
                    PlaygroundEventType.SYSTEM,
                    {
                        "message": f"Human denied action {action_name} for agent {agent.name}",
                        "action": action_name,
                        "status": "denied_by_human",
                    },
                    agent_id=agent.id,
                    agent_name=agent.name,
                )

        # 7) Incident creation on blocked actions
        if agent.last_verdict in ("DENY", "BLOCK", "QUARANTINE"):
            await self._create_incident_from_action(agent, action_name, agent.current_metadata)

        # 8) Mismatch detection (false negative)
        if action_obj and action_obj.is_malicious and agent.last_verdict == "ALLOW":
            await self._emit_event(
                PlaygroundEventType.MISMATCH_DETECTED,
                {
                    "message": "Malicious action was ALLOWED by Judge",
                    "action": action_name,
                    "agent": agent.name,
                },
                agent_id=agent.id,
                agent_name=agent.name,
            )

        # 9) Final status event
        final_status = "allowed"
        if agent.last_verdict in ("DENY", "BLOCK"):
            final_status = "blocked"
        elif agent.last_verdict == "QUARANTINE":
            final_status = "quarantined"

        await self._emit_event(
            PlaygroundEventType.SYSTEM,
            {
                "message": f"Action {action_name} {final_status}",
                "action": action_name,
                "status": final_status,
                "declared_intent": action_name,
                "detected_verdict": agent.last_verdict,
                "mismatch": (action_obj.is_malicious if action_obj else False) and agent.last_verdict == "ALLOW",
            },
            agent_id=agent.id,
            agent_name=agent.name,
        )

        # Status update broadcast moved to the unified block below

        # Update mirrored Agent record with tick results
        scoped_id = f"pg-{self.session_id[:8]}-{agent.name}"
        async with AsyncSessionLocal() as agent_db:
            result = await agent_db.execute(
                select(Agent).where(Agent.system_id == scoped_id)
            )
            agent_record = result.scalar_one_or_none()
            if agent_record:
                agent_record.last_seen = utc_now()
                agent_record.judge_decision_count += 1

                if agent.last_verdict in ("DENY", "BLOCK", "QUARANTINE"):
                    agent_record.incident_count += 1
                    agent_record.health_score = max(0, agent_record.health_score - 5)
                else:
                    # Gradually recover health on ALLOW instead of resetting to 100
                    agent_record.health_score = min(100, (agent_record.health_score or 0) + 1)

                # Compute standard status for DB + WebSocket
                hs = agent_record.health_score or 0
                if hs >= 80:
                    agent_record.status = "online"
                elif hs >= 50:
                    agent_record.status = "degraded"
                else:
                    agent_record.status = "offline"

                bypass_patterns = verdict.get("bypass_patterns_detected", [])
                if bypass_patterns:
                    agent_record.bypass_attempt_count += len(bypass_patterns)

                await agent_db.commit()

                # Broadcast unified status update with standard status labels
                await ws_manager.broadcast({
                    "event_type": "agent_status_updated",
                    "agent_id": scoped_id,
                    "system_id": scoped_id,
                    "agent_name": agent.name,
                    "status": agent_record.status,
                    "health_score": hs,
                })

        return {
            "verdict": agent.last_verdict,
            "action_name": action_name,
            "reasoning": reasoning,
            "situation": situation,
            "is_malicious": action_obj.is_malicious if action_obj else False,
            "final_status": final_status,
        }

    async def _create_incident_from_action(
        self, agent: SimulatedAgent, action_name: str, metadata: dict
    ) -> None:
        """Create a real incident in the database from a blocked playground action."""
        try:
            normalized_event = normalize_event(
                {
                    "event_id": str(uuid.uuid4()),
                    "timestamp": time.time(),
                    "source": "playground",
                    "agent_id": agent.name,
                    "session_id": self.session_id,
                    "action_type": action_name,
                    "metadata": metadata,
                },
                source_hint="playground",
            )

            detection = DetectionEngine().evaluate(normalized_event)

            # Override detection with playground metadata when available
            meta_type = metadata.get("incident_type")
            if meta_type and meta_type in INCIDENT_TYPES:
                detection.incident_type = meta_type
                detection.incident_type_name = INCIDENT_TYPES[meta_type]
                detection.severity = metadata.get("severity", detection.severity)
                detection.confidence = metadata.get("confidence", detection.confidence)
                detection.anomaly_score = min(detection.confidence * 100, 100.0)
                detection.deterministic = True
                prefix = meta_type.rsplit("-", 1)[0] if "-" in meta_type else meta_type
                detection.category = {
                    "AGT-DEL": "integrity",
                    "AGT-FIN": "financial",
                    "AGT-PER": "access",
                    "AGT-HRM": "safety",
                    "AGT-EXT": "exfiltration",
                    "AGT-INJ": "injection",
                    "AGT-HAL": "reliability",
                    "AGT-CRE": "secrets",
                    "AGT-RAT": "availability",
                    "AGT-DRF": "model",
                    "AGT-TLM": "misuse",
                    "AGT-GAP": "coverage",
                    "AGT-SPY": "reconnaissance",
                    "AGT-BYP": "bypass",
                    "AGT-PRV": "privacy",
                    "AGT-REG": "compliance",
                }.get(prefix, "unknown")

            async with AsyncSessionLocal() as db:
                incident = await IncidentFactory.create_incident(db, normalized_event, detection)
                await db.flush()

                # Create JudgeDecision record and link to incident
                vdata = agent.last_verdict_data or {}
                if vdata.get("verdict"):
                    decision = JudgeDecision(
                        decision_id=f"JDG-{uuid.uuid4().hex[:12].upper()}",
                        incident_id=incident.id,
                        agent_id=agent.name,
                        verdict=vdata.get("verdict", "ESCALATE"),
                        severity_score=vdata.get("severity_score", 0),
                        confidence=vdata.get("confidence", 1.0),
                        matched_rules=vdata.get("matched_rules", []),
                        bypass_patterns_detected=vdata.get("bypass_patterns_detected", []),
                        rationale=vdata.get("rationale", ""),
                        latency_ms=vdata.get("latency_ms", 0.0),
                    )
                    db.add(decision)
                    await db.flush()
                    incident.judge_decision_id = decision.id
                await db.commit()

            await ws_manager.broadcast({
                "event_type": "incident_detected",
                "incident_id": incident.incident_id,
                "severity": incident.severity,
                "category": incident.category,
                "incident_type": incident.incident_type,
                "confidence": incident.confidence,
                "timestamp": incident.created_at.isoformat(),
            })

            # In-app notification + email alert
            await ws_manager.broadcast({
                "event_type": "notification",
                "notification_type": "incident",
                "title": f"Playbook Alert: {incident.incident_type}",
                "message": (
                    f"Agent {agent.name} triggered {incident.incident_type} "
                    f"({incident.severity}) in session {self.session_id[:8]}."
                ),
                "severity": incident.severity,
                "incident_id": incident.incident_id,
                "agent_name": agent.name,
                "session_id": self.session_id,
                "created_at": incident.created_at.isoformat(),
            })

            # Send email alert asynchronously (fail-open)
            async def _send_email_alert():
                try:
                    from app.services.notification_service import NotificationService
                    service = NotificationService()
                    msg = {
                        "title": f"PLAYBOOK Alert: {incident.severity.upper()} {incident.incident_type}",
                        "body": (
                            f"Incident: {incident.incident_id}\n"
                            f"Agent: {agent.name}\n"
                            f"Session: {self.session_id[:8]}\n"
                            f"Severity: {incident.severity}\n"
                            f"Category: {incident.category}\n"
                            f"Confidence: {incident.confidence:.2f}\n"
                            f"Action: {action_name}"
                        ),
                        "severity": incident.severity,
                        "incident_id": incident.incident_id,
                    }
                    await service.send("email", msg)
                    await service.close()
                except Exception:
                    pass

            asyncio.create_task(_send_email_alert())

            await self._emit_event(
                PlaygroundEventType.INCIDENT_CREATED,
                {
                    "incident_id": incident.incident_id,
                    "action": action_name,
                    "agent": agent.name,
                    "severity": incident.severity,
                },
                agent_id=agent.id,
                agent_name=agent.name,
            )
        except Exception as exc:
            await self._emit_event(
                PlaygroundEventType.ERROR,
                {"error": f"Failed to create incident: {exc}"},
                agent_id=agent.id,
                agent_name=agent.name,
            )

    async def _emit_event(
        self,
        event_type: PlaygroundEventType,
        payload: dict,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> None:
        """Persist event to DB and broadcast via WebSocket."""
        event_id = str(uuid.uuid4())
        event_data = {
            "event_id": event_id,
            "event_type": event_type.value,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "payload": payload,
            "timestamp": asyncio.get_event_loop().time(),
        }

        # Broadcast to WebSocket clients
        await ws_manager.broadcast({
            "type": "playground_event",
            "session_id": self.session_id,
            **event_data,
        })

        # Persist to database (fire-and-forget to not block the loop)
        async def _persist():
            try:
                async with AsyncSessionLocal() as db:
                    db_event = PlaygroundEvent(
                        session_id=self.session_id,
                        agent_id=agent_id,
                        agent_name=agent_name,
                        event_type=event_type,
                        payload=payload,
                    )
                    db.add(db_event)
                    await db.commit()
            except Exception:
                pass

        task = asyncio.create_task(_persist())
        task.add_done_callback(
            lambda t: print(f"[playground] Persist task error: {t.exception()}") if t.done() and t.exception() else None
        )


# Global engine registry (one engine per session)
_engines: dict[str, PlaygroundEngine] = {}


def get_engine(session_id: str) -> Optional[PlaygroundEngine]:
    return _engines.get(session_id)


def set_engine(session_id: str, engine: PlaygroundEngine) -> None:
    _engines[session_id] = engine


def remove_engine(session_id: str) -> None:
    _engines.pop(session_id, None)
