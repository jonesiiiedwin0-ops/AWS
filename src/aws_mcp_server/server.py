"""Core server wiring for the AWS MCP Server.

This module is intentionally dependency-light. The actual MCP transport and the
boto3-backed service handlers are wired in lazily so that the package can be
imported, version-checked, and unit-tested without optional dependencies
installed.
"""

from __future__ import annotations

import logging

from .config import Config

logger = logging.getLogger("aws_mcp_server")


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def build_server(config: Config):
    """Construct (but do not start) the MCP server for the given config.

    Returns a lightweight description object today. As service handlers land,
    this becomes the place where the MCP server instance is created and tools
    are registered for each enabled service.
    """
    logger.info(
        "Configuring AWS MCP Server | region=%s read_only=%s services=%s",
        config.region,
        config.read_only,
        ",".join(config.enabled_services),
    )
    return _ServerHandle(config)


class _ServerHandle:
    """Placeholder handle representing a configured-but-not-running server."""

    def __init__(self, config: Config) -> None:
        self.config = config

    def run(self) -> None:  # pragma: no cover - requires MCP transport
        raise NotImplementedError(
            "The MCP transport and service handlers are not implemented yet. "
            "Track progress in STRATEGY.md (Phase 1 — MVP)."
        )
