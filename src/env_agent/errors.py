"""Error types for the environment variable agent."""

from typing import Any, Dict, Optional


class EnvAgentError(Exception):
    """Base error raised by the environment variable agent.

    Carries a stable machine-readable ``code`` and an optional structured
    ``detail`` payload so callers can build JSON error responses without
    string matching.
    """

    code: str = "agent_error"

    def __init__(
        self,
        message: str,
        detail: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.detail: Dict[str, Any] = detail or {}

    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": self.message, "detail": self.detail}


class ValidationError(EnvAgentError):
    """Raised when a command or payload fails schema validation."""

    code = "validation_error"


class NotFoundError(EnvAgentError):
    """Raised when a referenced variable does not exist."""

    code = "not_found"


class ConflictError(EnvAgentError):
    """Raised when an operation conflicts with the current state."""

    code = "conflict"


class StorageError(EnvAgentError):
    """Raised when JSON persistence fails (read/write/parse)."""

    code = "storage_error"
