"""JSON persistence for the environment variable agent.

The store keeps the agent state as a single JSON document on disk, written
atomically to avoid corruption on interrupted writes. This is the only
supported persistence format (JSON only).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from env_agent.errors import StorageError
from env_agent.models import EnvState, PHASE, SCHEMA_VERSION


class JsonStore:
    """Atomic JSON file store for an :class:`EnvState` document."""

    def __init__(self, path: Optional[str] = None) -> None:
        self._path = Path(path) if path else None

    @property
    def path(self) -> Optional[Path]:
        return self._path

    def exists(self) -> bool:
        return self._path is not None and self._path.is_file()

    def load(self) -> EnvState:
        if self._path is None:
            raise StorageError("store has no configured path")
        if not self._path.is_file():
            return EnvState(schema_version=SCHEMA_VERSION, phase=PHASE, variables={})
        try:
            raw = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"failed to read store: {exc}") from exc
        try:
            return EnvState.from_json(raw)
        except Exception as exc:
            raise StorageError(f"store failed validation: {exc}") from exc

    def save(self, state: EnvState) -> None:
        if self._path is None:
            raise StorageError("store has no configured path")
        try:
            serialized = state.to_json(indent=2)
        except Exception as exc:
            raise StorageError(f"failed to serialize state: {exc}") from exc
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self._path.parent), suffix=".tmp", prefix=f".{self._path.name}"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(serialized)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, self._path)
        except OSError as exc:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise StorageError(f"failed to write store: {exc}") from exc

    def clear(self) -> None:
        if self._path is not None and self._path.is_file():
            try:
                self._path.unlink()
            except OSError as exc:
                raise StorageError(f"failed to clear store: {exc}") from exc
