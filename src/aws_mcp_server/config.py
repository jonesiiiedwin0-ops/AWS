"""Configuration loading for the AWS MCP Server.

Configuration is read from environment variables so the server works with the
standard 12-factor / container workflow and the AWS credential chain. This
module has no third-party dependencies so it can be imported and tested without
boto3 or an AWS account.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_REGION = "us-east-1"
DEFAULT_SERVICES = ("s3", "ec2")
DEFAULT_LOG_LEVEL = "INFO"

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    value = raw.strip().lower()
    if value in _TRUTHY:
        return True
    if value in _FALSY:
        return False
    raise ValueError(f"{name} must be a boolean-like value, got {raw!r}")


def _env_services(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    services = tuple(s.strip().lower() for s in raw.split(",") if s.strip())
    return services or default


@dataclass(frozen=True)
class Config:
    """Resolved server configuration."""

    region: str = DEFAULT_REGION
    read_only: bool = True
    enabled_services: tuple[str, ...] = field(default_factory=lambda: DEFAULT_SERVICES)
    log_level: str = DEFAULT_LOG_LEVEL

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> Config:
        """Build a Config from environment variables.

        Pass ``environ`` to load from a specific mapping (useful in tests);
        defaults to ``os.environ``.
        """
        # Temporarily swap os.environ view only if a custom mapping is given.
        if environ is None:
            return cls(
                region=os.environ.get("AWS_REGION", DEFAULT_REGION),
                read_only=_env_bool("AWS_MCP_READ_ONLY", True),
                enabled_services=_env_services("AWS_MCP_ENABLED_SERVICES", DEFAULT_SERVICES),
                log_level=os.environ.get("AWS_MCP_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
            )

        def get(key: str, default: str) -> str:
            return environ.get(key, default)

        read_only_raw = environ.get("AWS_MCP_READ_ONLY", "")
        read_only = True
        if read_only_raw.strip():
            value = read_only_raw.strip().lower()
            if value in _TRUTHY:
                read_only = True
            elif value in _FALSY:
                read_only = False
            else:
                raise ValueError(f"AWS_MCP_READ_ONLY must be boolean-like, got {read_only_raw!r}")

        services_raw = environ.get("AWS_MCP_ENABLED_SERVICES", "")
        services = tuple(s.strip().lower() for s in services_raw.split(",") if s.strip())

        return cls(
            region=get("AWS_REGION", DEFAULT_REGION),
            read_only=read_only,
            enabled_services=services or DEFAULT_SERVICES,
            log_level=get("AWS_MCP_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
        )
