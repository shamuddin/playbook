"""Framework middleware integrations for PLAYBOOK SDK."""

# Optional integrations are imported lazily to avoid hard dependencies


def __getattr__(name: str):
    if name == "PlaybookCallbackHandler":
        from .langchain import PlaybookCallbackHandler

        return PlaybookCallbackHandler
    if name == "crewai_guard":
        from .crewai import crewai_guard

        return crewai_guard
    if name == "CrewAIGuard":
        from .crewai import CrewAIGuard

        return CrewAIGuard
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["PlaybookCallbackHandler", "crewai_guard", "CrewAIGuard"]
