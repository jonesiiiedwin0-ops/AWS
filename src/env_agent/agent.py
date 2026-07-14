"""Core engine for the environment variable agent.

``EnvAgent`` owns an in-memory :class:`EnvState` and exposes a single
``handle`` method that accepts an :class:`EnvCommand` and returns an
:class:`EnvResponse`. A thin ``handle_json`` wrapper accepts and returns
JSON strings so the agent can be driven entirely through JSON.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional

from env_agent.errors import (
    ConflictError,
    EnvAgentError,
    NotFoundError,
    StorageError,
    ValidationError,
)
from env_agent.models import (
    EnvCommand,
    EnvResponse,
    EnvState,
    EnvVariable,
    ValidationError,
    is_valid_variable_name,
    _MASK,
)
from env_agent.store import JsonStore


class EnvAgent:
    """JSON-driven environment variable manager."""

    def __init__(self, store: Optional[JsonStore] = None) -> None:
        self._state = EnvState()
        self._store = store

    @property
    def state(self) -> EnvState:
        return self._state

    @property
    def store(self) -> Optional[JsonStore]:
        return self._store

    def handle_json(self, raw: str) -> str:
        try:
            command = EnvCommand.from_json(raw)
        except ValidationError as exc:
            return EnvResponse.from_error(exc).to_json()
        return self.handle(command).to_json()

    def handle(self, command: EnvCommand) -> EnvResponse:
        handler = self._DISPATCH.get(command.action)
        if handler is None:
            return EnvResponse.error(
                action=command.action,
                code="unknown_action",
                message=f"unknown action: {command.action!r}",
                request_id=command.request_id,
            )
        try:
            data = handler(self, command.args)
        except EnvAgentError as exc:
            return EnvResponse.from_error(
                exc, action=command.action, request_id=command.request_id
            )
        except Exception as exc:  # defensive: never leak raw traces as success
            return EnvResponse.error(
                action=command.action,
                code="internal_error",
                message=str(exc),
                request_id=command.request_id,
            )
        return EnvResponse.ok(
            action=command.action, data=data, request_id=command.request_id
        )

    def set_var(self, args: Dict[str, Any]) -> Dict[str, Any]:
        key = self._require_key(args)
        if "value" not in args:
            raise ValidationError("missing required arg 'value'")
        secret = bool(args.get("secret", False))
        description = args.get("description")
        if description is not None and not isinstance(description, str):
            raise ValidationError("'description' must be a string")
        variable = EnvVariable.from_dict(
            {"value": args["value"], "secret": secret, "description": description}
        )
        previous = self._state.variables.get(key)
        self._state.variables[key] = variable
        return {
            "key": key,
            "created": previous is None,
            "secret": variable.secret,
            "updated_at": variable.updated_at,
        }

    def get_var(self, args: Dict[str, Any]) -> Dict[str, Any]:
        key = self._require_key(args)
        variable = self._state.variables.get(key)
        if variable is None:
            raise NotFoundError(f"variable not found: {key!r}", detail={"key": key})
        return {
            "key": key,
            "value": variable.value,
            "secret": variable.secret,
            "description": variable.description,
            "updated_at": variable.updated_at,
        }

    def list_vars(self, args: Dict[str, Any]) -> Dict[str, Any]:
        include_secrets = bool(args.get("include_secrets", True))
        items = {}
        for key, variable in self._state.variables.items():
            value = variable.value
            if variable.secret and not include_secrets:
                value = _MASK
            items[key] = {
                "value": value,
                "secret": variable.secret,
                "description": variable.description,
                "updated_at": variable.updated_at,
            }
        return {"count": len(items), "variables": items}

    def delete_var(self, args: Dict[str, Any]) -> Dict[str, Any]:
        key = self._require_key(args)
        if key not in self._state.variables:
            raise NotFoundError(f"variable not found: {key!r}", detail={"key": key})
        del self._state.variables[key]
        return {"key": key, "deleted": True}

    def has_var(self, args: Dict[str, Any]) -> Dict[str, Any]:
        key = self._require_key(args)
        return {"key": key, "exists": key in self._state.variables}

    def clear_vars(self, args: Dict[str, Any]) -> Dict[str, Any]:
        count = len(self._state.variables)
        self._state.variables.clear()
        return {"cleared": count}

    def dump_state(self, args: Dict[str, Any]) -> Dict[str, Any]:
        include_secrets = bool(args.get("include_secrets", True))
        return self._state_to_public(include_secrets=include_secrets)

    def load_state(self, args: Dict[str, Any]) -> Dict[str, Any]:
        if "state" in args:
            payload = args["state"]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError as exc:
                    raise ValidationError(f"state must be valid JSON: {exc}")
            self._state = EnvState.from_dict(payload)
            return {"loaded": "inline", "count": len(self._state.variables)}
        if self._store is not None:
            self._state = self._store.load()
            return {"loaded": "store", "count": len(self._state.variables)}
        raise ConflictError("no state provided and no store configured")

    def save_state(self, args: Dict[str, Any]) -> Dict[str, Any]:
        if self._store is None:
            raise ConflictError("no store configured; cannot save")
        self._store.save(self._state)
        return {"saved": True, "path": str(self._store.path)}

    def export_vars(self, args: Dict[str, Any]) -> Dict[str, Any]:
        include_secrets = bool(args.get("include_secrets", True))
        out: Dict[str, str] = {}
        for key, variable in self._state.variables.items():
            if variable.secret and not include_secrets:
                continue
            out[key] = variable.value
        return {"count": len(out), "variables": out}

    def _require_key(self, args: Dict[str, Any]) -> str:
        key = args.get("key")
        if not isinstance(key, str) or not key:
            raise ValidationError("missing required arg 'key'")
        if not is_valid_variable_name(key):
            raise ValidationError(f"invalid variable name: {key!r}")
        return key

    def _state_to_public(self, *, include_secrets: bool) -> Dict[str, Any]:
        variables = {}
        for key, variable in self._state.variables.items():
            value = variable.value
            if variable.secret and not include_secrets:
                value = _MASK
            variables[key] = {
                "value": value,
                "secret": variable.secret,
                "description": variable.description,
                "updated_at": variable.updated_at,
            }
        return {
            "schema_version": self._state.schema_version,
            "phase": self._state.phase,
            "variables": variables,
        }

    _DISPATCH: Dict[str, Callable[["EnvAgent", Dict[str, Any]], Dict[str, Any]]] = {
        "set": set_var,
        "get": get_var,
        "list": list_vars,
        "delete": delete_var,
        "has": has_var,
        "clear": clear_vars,
        "dump": dump_state,
        "load": load_state,
        "save": save_state,
        "export": export_vars,
    }
