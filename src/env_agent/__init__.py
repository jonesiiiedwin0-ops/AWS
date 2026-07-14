"""Environment Variable Agent - phase 1 of 800.

A self-contained agent that manages environment variables through a strict
JSON command/response protocol. The agent's entire state and communication
surface is JSON; no YAML, TOML, or ``.env`` parsing is involved.

Phase 1 establishes the foundation:

* a JSON schema for the agent state and its variables,
* a JSON persistence layer (atomic file writes),
* a JSON command/response engine (``EnvAgent``),
* a JSON-only CLI that speaks to the agent over stdin/stdout.
"""

from env_agent.agent import EnvAgent
from env_agent.errors import EnvAgentError
from env_agent.models import (
    EnvCommand,
    EnvResponse,
    EnvState,
    EnvVariable,
)

__version__ = "0.1.0"
__phase__ = "phase-1"

__all__ = [
    "EnvAgent",
    "EnvAgentError",
    "EnvCommand",
    "EnvResponse",
    "EnvState",
    "EnvVariable",
    "__version__",
    "__phase__",
]
