# PLAYBOOK Python SDK

Runtime safety for AI agents. Guard your agent actions with the PLAYBOOK Judge Layer.

## Installation

```bash
pip install playbook-guard
```

## Quick Start

```python
import playbook_sdk

# Initialize with your PLAYBOOK endpoint and API key
playbook_sdk.init(
    endpoint="https://playbook.yourcompany.com",
    api_key="your-api-key",
)

@playbook_sdk.guard(agent_id="customer-service-agent-01")
def process_customer_request(customer_id: str, request: str):
    """This function is now protected by the Judge Layer."""
    # If the Judge detects a risky pattern (e.g., PII leak attempt),
    # a GuardBlockedError is raised before this code runs.
    return agent.run(customer_id, request)
```

## Features

- **@guard decorator** — Automatically evaluates agent actions through the Judge Layer
- **Heartbeat monitoring** — Background health reporting for long-running agents
- **Incident reporting** — Programmatic incident creation from agent code
- **Framework integrations** — Optional LangChain and CrewAI middleware

## Configuration

Environment variables:

```bash
export PLAYBOOK_ENDPOINT="https://playbook.yourcompany.com"
export PLAYBOOK_API_KEY="your-api-key"
export PLAYBOOK_TIMEOUT="5.0"
export PLAYBOOK_HEARTBEAT_INTERVAL="60.0"
```

## Advanced Usage

### Custom block handler

```python
from playbook_sdk import guard
from playbook_sdk.exceptions import GuardBlockedError

async def on_block(verdict, *args, **kwargs):
    print(f"Blocked: {verdict['reason']}")
    return {"error": "Action blocked by safety policy"}

@guard(agent_id="agent-001", on_block=on_block)
async def risky_action(data):
    return await process(data)
```

### Heartbeat monitoring

```python
from playbook_sdk import HeartbeatSender

heartbeat = HeartbeatSender(agent_id="agent-001", interval=30.0)
heartbeat.start()

# ... agent runs ...

heartbeat.stop()
await heartbeat.close()
```

### Direct client usage

```python
from playbook_sdk import PlaybookClient

client = PlaybookClient(endpoint="https://playbook.internal", api_key="key")

# Judge an action manually
verdict = await client.judge(
    agent_id="agent-001",
    action_type="tool_call",
    action_details={"tool": "delete_database", "args": ["production"]},
)
print(verdict["verdict"])  # BLOCK

await client.close()
```

## Framework Integrations

### LangChain

Install the optional dependency:

```bash
pip install playbook-guard[langchain]
```

Use the callback handler to judge every tool and LLM call:

```python
from playbook_sdk.middleware.langchain import PlaybookCallbackHandler
from langchain.agents import initialize_agent

handler = PlaybookCallbackHandler(agent_id="customer-service-agent-01")

agent = initialize_agent(
    tools,
    llm,
    callbacks=[handler],
)
```

The handler intercepts `on_tool_start` and `on_llm_start`, sends action
metadata to the Judge Layer, and raises `GuardBlockedError` or
`GuardQuarantinedError` before the action executes.

> **Note:** The callback handler uses `asyncio.run()` internally and works
> best with **synchronous** LangChain chains. For async chains, apply
> `@playbook_sdk.guard` to individual tools instead.

### CrewAI

Install the optional dependency:

```bash
pip install playbook-guard[crewai]
```

Wrap CrewAI tasks with the guard decorator:

```python
from playbook_sdk.middleware.crewai import crewai_guard
from crewai import task

@crewai_guard(agent_id="researcher-001")
@task
def research_task(agent):
    return agent.run("Find latest AI safety papers")
```

The decorator automatically extracts the agent ID from the CrewAI
`Agent.role` attribute when the task receives an agent argument.

## Verdicts

The Judge Layer returns one of these verdicts:

- `ALLOW` — Action is safe, proceed normally
- `BLOCK` — Action is dangerous, raise `GuardBlockedError`
- `QUARANTINE` — Action is suspicious, raise `GuardQuarantinedError`
- `ESCALATE` / `HUMAN_REVIEW` — Action requires human review, proceed with logging
