"""JSON schema for the environment variable agent.

This module is intentionally implemented with the Python standard library
only (``dataclasses`` + ``json``). The agent is "JSON only": its entire
state, command, and response surface is expressed as JSON documents, with no
external framework or configuration format involved.

Public document shapes
-----------------------
EnvVariable (object):
    {
      "value":      "<string>",
      "secret":     <bool, optional, default false>,
      "description": "<string|null, optional>",
      "updated_at": "<string, UTC ISO-8601>"
    }

EnvState (object):
    {
      "schema_version": <int, default 1>,
      "phase":          "<string, default 'phase-1'>",
      "variables":      { "<name>": EnvVariable, ... }
    }

EnvCommand (object):
    {
      "action":     "<string>",
      "args":       { ... },
      "request_id": "<string|null, optional>"
    }

EnvResponse (object):
    {
      "request_id": "<string|null>",
      "status":     "ok" | "error",
      "action":     "<string|null>",
      "data":       <any|null>,
      "error":      { "code": "...", "message": "...", "detail": {} } | null
    }
"""

from __future__ import annotations

import datetime
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from env_agent.errors import ValidationError

SCHEMA_VERSION: int = 1
PHASE: str = "phase-1"
_MASK: str = "********"
_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _coerce_to_str(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def is_valid_variable_name(name: str) -> bool:
    """Return True when ``name`` is a valid environment variable name."""
    return isinstance(name, str) and bool(_KEY_PATTERN.match(name))


@dataclass
class EnvVariable:
    value: str
    secret: bool = False
    description: Optional[str] = None
    updated_at: str = field(default_factory=_now_iso)

    @classmethod
    def from_dict(cls, data: Any) -> "EnvVariable":
        if not isinstance(data, dict):
            raise ValidationError(f"variable must be an object, got {type(data).__name__}")
        if "value" not in data:
            raise ValidationError("variable missing required field 'value'")
        value = _coerce_to_str(data["value"])
        secret = data.get("secret", False)
        if not isinstance(secret, bool):
            raise ValidationError("'secret' must be a boolean")
        description = data.get("description", None)
        if description is not None and not isinstance(description, str):
            raise ValidationError("'description' must be a string")
        updated_at = data.get("updated_at", _now_iso())
        if not isinstance(updated_at, str):
            raise ValidationError("'updated_at' must be a string")
        return cls(value=value, secret=secret, description=description, updated_at=updated_at)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "secret": self.secret,
            "description": self.description,
            "updated_at": self.updated_at,
        }


@dataclass
class EnvState:
    schema_version: int = SCHEMA_VERSION
    phase: str = PHASE
    variables: Dict[str, EnvVariable] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Any) -> "EnvState":
        if not isinstance(data, dict):
            raise ValidationError(f"state must be an object, got {type(data).__name__}")
        schema_version = data.get("schema_version", SCHEMA_VERSION)
        if not isinstance(schema_version, int):
            raise ValidationError("'schema_version' must be an integer")
        phase = data.get("phase", PHASE)
        if not isinstance(phase, str):
            raise ValidationError("'phase' must be a string")
        raw_vars = data.get("variables", {})
        if not isinstance(raw_vars, dict):
            raise ValidationError("'variables' must be an object")
        variables: Dict[str, EnvVariable] = {}
        for key, var in raw_vars.items():
            if not isinstance(key, str):
                raise ValidationError("variable keys must be strings")
            if not is_valid_variable_name(key):
                raise ValidationError(f"invalid variable name: {key!r}")
            variables[key] = EnvVariable.from_dict(var)
        return cls(schema_version=schema_version, phase=phase, variables=variables)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "phase": self.phase,
            "variables": {k: v.to_dict() for k, v in self.variables.items()},
        }

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_json(cls, raw: str) -> "EnvState":
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"invalid JSON: {exc}") from exc
        return cls.from_dict(payload)


@dataclass
class EnvCommand:
    action: str
    args: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Any) -> "EnvCommand":
        if not isinstance(data, dict):
            raise ValidationError(f"command must be an object, got {type(data).__name__}")
        action = data.get("action")
        if not isinstance(action, str) or not action.strip():
            raise ValidationError("command requires a non-empty 'action' string")
        args = data.get("args", {})
        if not isinstance(args, dict):
            raise ValidationError("'args' must be an object")
        request_id = data.get("request_id", None)
        if request_id is not None and not isinstance(request_id, str):
            raise ValidationError("'request_id' must be a string")
        return cls(action=action.strip(), args=args, request_id=request_id)

    @classmethod
    def from_json(cls, raw: str) -> "EnvCommand":
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"invalid JSON: {exc}") from exc
        return cls.from_dict(payload)


@dataclass
class EnvResponse:
    status: str
    action: Optional[str] = None
    data: Any = None
    error: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

    @classmethod
    def ok(
        cls,
        *,
        action: Optional[str] = None,
        data: Any = None,
        request_id: Optional[str] = None,
    ) -> "EnvResponse":
        return cls(status="ok", action=action, data=data, error=None, request_id=request_id)

    @classmethod
    def error(
        cls,
        *,
        action: Optional[str] = None,
        code: str,
        message: str,
        detail: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> "EnvResponse":
        return cls(
            status="error",
            action=action,
            data=None,
            error={"code": code, "message": message, "detail": detail or {}},
            request_id=request_id,
        )

    @classmethod
    def from_error(cls, exc: EnvAgentError, *, action=None, request_id=None) -> "EnvResponse":
        return cls.error(
            action=action,
            code=exc.code,
            message=exc.message,
            detail=exc.detail,
            request_id=request_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "action": self.action,
            "data": self.data,
            "error": self.error,
        }

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)
