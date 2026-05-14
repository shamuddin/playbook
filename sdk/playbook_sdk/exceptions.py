"""Custom exceptions for the PLAYBOOK Python SDK."""


class PlaybookError(Exception):
    """Base exception for PLAYBOOK SDK."""
    pass


class GuardError(PlaybookError):
    """Raised when the guard encounters an unexpected error."""
    pass


class GuardBlockedError(GuardError):
    """Raised when the Judge Layer blocks an action."""
    pass


class GuardQuarantinedError(GuardError):
    """Raised when the Judge Layer quarantines an action."""
    pass


class GuardTimeoutError(GuardError):
    """Raised when the Judge Layer evaluation times out."""
    pass


class AuthenticationError(PlaybookError):
    """Raised when API authentication fails."""
    pass


class IncidentReportError(PlaybookError):
    """Raised when incident reporting fails."""
    pass
