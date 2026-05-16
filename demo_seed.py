#!/usr/bin/env python3
"""PLAYBOOK Demo Seed Script.

Pre-seeds the PLAYBOOK backend database via REST API calls and direct DB
insertion for fields the API doesn't yet expose (custom incident statuses
like "quarantined"/"blocked" and deterministic judge verdict distributions).

Requirements:
    - Backend running at http://localhost:8001/api/v1
    - Python environment with backend dependencies installed
      (httpx, sqlalchemy, and backend packages under backend/)
    - demo@playbook.local user exists in the DB

Usage:
    cd k:\\Hackthon\\Playbook\\PlaybookRepo
    python demo_seed.py
"""
import asyncio
import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Bootstrap backend environment
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")


def _load_backend_env() -> None:
    """Load backend/.env into os.environ so imports see the same config."""
    env_path = os.path.join(BACKEND_DIR, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key, val)


_load_backend_env()

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

HAS_BACKEND = False
try:
    from sqlalchemy import func, select
    from app.database import AsyncSessionLocal
    from app.models import Agent, Incident, IncidentMetadata, JudgeDecision, TimelineEvent

    HAS_BACKEND = True
except Exception as exc:  # pragma: no cover
    print(f"[WARN] Backend DB imports failed ({exc}). Direct DB inserts will be skipped.")

try:
    import httpx
except ImportError as exc:  # pragma: no cover
    print(f"[ERROR] httpx is required: {exc}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL = "http://localhost:8001/api/v1"
ADMIN_EMAIL = "demo@playbook.local"
ADMIN_PASSWORD = "demo123"

INCIDENT_TYPE_MAP = {
    "prompt_injection": "AGT-INJ-006",
    "data_exfiltration": "AGT-EXT-005",
    "privilege_escalation": "AGT-PER-003",
    "jailbreak_attempt": "AGT-BYP-014",
    "model_manipulation": "AGT-TLM-011",
    "benign_false_positive": "AGT-GAP-012",
}

CATEGORY_MAP = {
    "prompt_injection": "injection",
    "data_exfiltration": "exfiltration",
    "privilege_escalation": "escalation",
    "jailbreak_attempt": "bypass",
    "model_manipulation": "manipulation",
    "benign_false_positive": "false_positive",
}

BYPASS_PATTERNS = [
    "context_window_displacement",
    "indirect_tool_chaining",
    "unicode_homoglyphs",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class ApiClient:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        self.token: str | None = None

    async def login(self) -> None:
        resp = await self.client.post(
            "/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        resp.raise_for_status()
        payload = resp.json()
        self.token = payload["data"]["access_token"]
        self.client.headers["Authorization"] = f"Bearer {self.token}"
        print("[OK] Authenticated")

    async def get(self, path: str, **kwargs):
        return await self.client.get(path, **kwargs)

    async def post(self, path: str, **kwargs):
        return await self.client.post(path, **kwargs)

    async def put(self, path: str, **kwargs):
        return await self.client.put(path, **kwargs)

    async def close(self) -> None:
        await self.client.aclose()


def _generate_incident_id(dt: datetime) -> str:
    ts = dt.strftime("%Y%m%d-%H%M%S")
    return f"INC-{ts}-{uuid.uuid4().hex[:8].upper()}"


def _generate_decision_id() -> str:
    return f"JDG-{uuid.uuid4().hex[:12].upper()}"


def _naive(dt: datetime) -> datetime:
    """Strip tzinfo to match backend utc_now() format."""
    return dt.replace(tzinfo=None)


# ---------------------------------------------------------------------------
# 1. Agents
# ---------------------------------------------------------------------------
async def seed_agents(api: ApiClient) -> None:
    print("\n[1] Seeding agents...")
    agents_spec = [
        {
            "system_id": "athena",
            "name": "Athena",
            "description": json.dumps(
                {"model": "gpt-4", "department": "Customer Success", "type": "customer_support"}
            ),
            "health_score": 94,
        },
        {
            "system_id": "argus",
            "name": "Argus",
            "description": json.dumps(
                {"model": "claude-3", "department": "Risk", "type": "fraud_detection"}
            ),
            "health_score": 91,
        },
        {
            "system_id": "clerkbot",
            "name": "ClerkBot",
            "description": json.dumps(
                {"model": "llama-3", "department": "HR", "type": "hr_processor"}
            ),
            # NOTE: backend derives status from health_score:
            # >=80 healthy, >=50 degraded, else critical.
            # 70 yields "degraded" as requested for ClerkBot.
            "health_score": 70,
        },
    ]

    resp = await api.get("/agents")
    existing = {}
    if resp.status_code == 200:
        items = resp.json().get("data", {}).get("items", [])
        existing = {a["system_id"]: a for a in items}

    for spec in agents_spec:
        sid = spec["system_id"]
        if sid in existing:
            print(f"    SKIP Agent '{sid}' already exists")
            continue

        resp = await api.post(
            "/agents",
            params={
                "system_id": sid,
                "name": spec["name"],
                "description": spec["description"],
            },
        )
        if resp.status_code == 409:
            print(f"    SKIP Agent '{sid}' already exists (409)")
            continue
        resp.raise_for_status()
        agent_data = resp.json()["data"]
        print(f"    CREATED Agent '{sid}' ({agent_data['id']})")

        # Set health score via heartbeat
        resp = await api.post(
            f"/agents/{sid}/heartbeat",
            json={"health_score": spec["health_score"], "lie_rate": 0.0},
        )
        resp.raise_for_status()
        print(f"    HEARTBEAT '{sid}' -> health_score={spec['health_score']}")

    print("[OK] Agents seeded")


# ---------------------------------------------------------------------------
# 2. Incidents
# ---------------------------------------------------------------------------
async def seed_incidents_db() -> None:
    if not HAS_BACKEND:
        print("\n[SKIP] Backend DB unavailable; skipping incident seeding.")
        return

    print("\n[2] Seeding incidents via DB...")
    specs = [
        # (friendly_key, severity, status, response_status, count)
        ("prompt_injection", "critical", "quarantined", "completed", 2),
        ("data_exfiltration", "high", "blocked", "completed", 2),
        ("privilege_escalation", "critical", "escalated", "completed", 1),
        ("jailbreak_attempt", "medium", "resolved", "completed", 2),
        ("model_manipulation", "high", "resolved", "completed", 1),
        ("benign_false_positive", "low", "resolved", "completed", 2),
    ]

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(Incident.id)))
        if result.scalar() >= 8:
            print(f"    SKIP Already have {result.scalar()} incidents")
            return

        agent_result = await session.execute(select(Agent))
        agents = list(agent_result.scalars().all())

        now = datetime.now(timezone.utc)
        created_total = 0
        for key, severity, status, response_status, count in specs:
            inc_type = INCIDENT_TYPE_MAP[key]
            category = CATEGORY_MAP[key]
            for _ in range(count):
                created_at = now - timedelta(
                    days=random.randint(0, 6), hours=random.randint(0, 23)
                )
                agent = random.choice(agents) if agents else None

                incident = Incident(
                    id=str(uuid.uuid4()),
                    incident_id=_generate_incident_id(created_at),
                    event_id=f"evt-{uuid.uuid4().hex[:12]}",
                    status=status,
                    severity=severity,
                    category=category,
                    incident_type=inc_type,
                    confidence=round(random.uniform(0.75, 0.99), 2),
                    deterministic_classification=True,
                    response_status=response_status,
                    forensics_status="completed",
                    bypass_detected=(key in {"prompt_injection", "jailbreak_attempt"}),
                    created_at=_naive(created_at),
                    updated_at=_naive(created_at),
                )
                session.add(incident)
                await session.flush()

                meta = IncidentMetadata(
                    id=str(uuid.uuid4()),
                    incident_id=incident.id,
                    full_metadata_json={
                        "seeded_by": "demo_seed.py",
                        "agent_id": agent.system_id if agent else None,
                        "scenario": "demo",
                    },
                )
                session.add(meta)

                timeline = TimelineEvent(
                    id=str(uuid.uuid4()),
                    incident_id=incident.id,
                    timestamp=_naive(created_at),
                    stage="detect",
                    event_type="manual_creation",
                    event_description=f"Demo seeded incident: {key}",
                    source_component="demo_seed",
                    details_json={"severity": severity, "status": status},
                )
                session.add(timeline)
                created_total += 1

        await session.commit()
        print(f"    CREATED {created_total} incidents")


# ---------------------------------------------------------------------------
# 3. Judge Decisions
# ---------------------------------------------------------------------------
async def seed_judge_decisions() -> None:
    if not HAS_BACKEND:
        print("\n[SKIP] Backend DB unavailable; skipping judge decision seeding.")
        return

    print("\n[3] Seeding judge decisions via DB...")
    verdict_pool = (
        ["ALLOW"] * 60
        + ["DENY"] * 20
        + ["QUARANTINE"] * 15
        + ["ESCALATE"] * 5
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(JudgeDecision.id)))
        if result.scalar() >= 15:
            print(f"    SKIP Already have {result.scalar()} judge decisions")
            return

        agent_result = await session.execute(select(Agent))
        agents = list(agent_result.scalars().all())
        if not agents:
            print("    SKIP No agents found")
            return

        now = datetime.now(timezone.utc)
        created_total = 0
        for agent in agents:
            num = random.randint(5, 8)
            for _ in range(num):
                verdict = random.choice(verdict_pool)
                bp = (
                    random.sample(BYPASS_PATTERNS, k=random.randint(1, 2))
                    if random.random() < 0.35
                    else []
                )
                latency = round(random.uniform(15, 45), 2)
                created_at = now - timedelta(
                    days=random.randint(0, 6), hours=random.randint(0, 23)
                )

                decision = JudgeDecision(
                    id=str(uuid.uuid4()),
                    decision_id=_generate_decision_id(),
                    incident_id=f"INC-DEMO-{uuid.uuid4().hex[:8].upper()}",
                    agent_id=agent.system_id,
                    verdict=verdict,
                    severity_score=random.randint(1, 10),
                    confidence=1.0,
                    matched_rules=["demo_seed", f"severity_score:{random.randint(1, 10)}"],
                    bypass_patterns_detected=bp,
                    rationale=f"Demo seeded {verdict} decision for {agent.name}",
                    latency_ms=latency,
                    created_at=_naive(created_at),
                )
                session.add(decision)
                created_total += 1

        await session.commit()
        print(f"    CREATED {created_total} judge decisions")


# ---------------------------------------------------------------------------
# 4. Compliance
# ---------------------------------------------------------------------------
async def check_compliance(api: ApiClient) -> None:
    print("\n[4] Checking compliance frameworks...")
    resp = await api.get("/compliance/frameworks")
    if resp.status_code == 200:
        data = resp.json().get("data", {})
        frameworks = data.get("frameworks", [])
        names = [f["name"] for f in frameworks]
        print(f"    FOUND {len(frameworks)} framework(s): {names}")
    else:
        print(f"    WARN Could not fetch frameworks ({resp.status_code})")


# ---------------------------------------------------------------------------
# 5. Policy Builder ODPs
# ---------------------------------------------------------------------------
async def seed_policy_builder_odps(api: ApiClient) -> None:
    print("\n[5] Seeding Policy Builder ODPs...")
    specs = [
        {
            "incident_type": "AGT-INJ-006",  # prompt_injection
            "odps": {
                "auto_contain_enabled": "true",
                "escalation_contacts": "ciso@finserve.ai",
            },
        },
        {
            "incident_type": "AGT-EXT-005",  # data_exfiltration
            "odps": {
                "auto_contain_enabled": "true",
                "forensic_level": "maximum",
            },
        },
        {
            "incident_type": "AGT-PER-003",  # privilege_escalation
            "odps": {
                "auto_contain_enabled": "false",
                "requires_human_review": "true",
            },
        },
    ]

    for spec in specs:
        resp = await api.put(
            f"/policy-builder/odps/{spec['incident_type']}",
            json={"odps": spec["odps"], "skip_validation": False},
        )
        if resp.status_code in (200, 201):
            print(f"    UPDATED ODPs for {spec['incident_type']}")
        elif resp.status_code == 404:
            print(f"    SKIP Baseline not found for {spec['incident_type']}")
        else:
            print(f"    FAIL {spec['incident_type']}: {resp.status_code} {resp.text}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main() -> None:
    api = ApiClient()
    try:
        await api.login()
        await seed_agents(api)
        await seed_incidents_db()
        await seed_judge_decisions()
        await check_compliance(api)
        await seed_policy_builder_odps(api)
        print("\n[DONE] Demo seed complete.")
    except httpx.HTTPStatusError as exc:
        print(f"\n[ERROR] HTTP {exc.response.status_code}: {exc.response.text}")
        raise
    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())
