"""Core server wiring for the AWS MCP Server.

This module builds a real `Model Context Protocol <https://modelcontextprotocol.io>`_
server (via the official ``mcp`` SDK's :class:`~mcp.server.fastmcp.FastMCP`) and
registers one read-only tool group per enabled AWS service.

Design notes:

* **Read-only by default.** Only non-mutating tools are registered. Mutating
  actions stay gated behind ``read_only=False`` and are not implemented yet, so
  there is no path to an accidental write today.
* **Lazy boto3 session.** The session is created once per server build but makes
  no AWS calls until a tool is actually invoked, so the server can be built and
  introspected (``--list-tools``) without credentials.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .config import Config
from .services import ec2, s3

if TYPE_CHECKING:  # pragma: no cover - typing only
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("aws_mcp_server")

# Services that have read-only handlers wired up today. Anything enabled in
# config but not present here is reported as unsupported rather than silently
# ignored.
SUPPORTED_SERVICES = frozenset({"s3", "ec2"})


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def build_server(config: Config) -> FastMCP:
    """Construct (but do not start) the MCP server for the given config.

    Tools are registered for each enabled, supported service. The returned
    :class:`FastMCP` instance is started by the caller via ``.run()``.
    """
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("aws-mcp-server")
    session = _make_session(config.region)

    requested = list(config.enabled_services)
    unsupported = [svc for svc in requested if svc not in SUPPORTED_SERVICES]
    if unsupported:
        logger.warning(
            "Ignoring not-yet-supported services: %s (supported: %s)",
            ", ".join(unsupported),
            ", ".join(sorted(SUPPORTED_SERVICES)),
        )

    if "s3" in requested:
        _register_s3(mcp, session)
    if "ec2" in requested:
        _register_ec2(mcp, session)

    logger.info(
        "Configured AWS MCP Server | region=%s read_only=%s services=%s",
        config.region,
        config.read_only,
        ",".join(svc for svc in requested if svc in SUPPORTED_SERVICES) or "(none)",
    )
    return mcp


def _make_session(region: str) -> Any:
    import boto3

    return boto3.Session(region_name=region)


def _register_s3(mcp: FastMCP, session: Any) -> None:
    @mcp.tool()
    def s3_list_buckets() -> dict:
        """List all S3 buckets in the account (read-only)."""
        return s3.list_buckets(session)

    @mcp.tool()
    def s3_list_objects(bucket: str, prefix: str = "", max_keys: int = 100) -> dict:
        """List objects in an S3 bucket, optionally filtered by prefix (read-only)."""
        return s3.list_objects(session, bucket, prefix=prefix, max_keys=max_keys)

    @mcp.tool()
    def s3_bucket_summary(bucket: str) -> dict:
        """Summarize object count and total size for an S3 bucket (read-only, sampled)."""
        return s3.bucket_summary(session, bucket)


def _register_ec2(mcp: FastMCP, session: Any) -> None:
    @mcp.tool()
    def ec2_describe_instances(region: str = "") -> dict:
        """Describe EC2 instances, one record per instance (read-only)."""
        return ec2.describe_instances(session, region=region or None)

    @mcp.tool()
    def ec2_instance_state_counts(region: str = "") -> dict:
        """Count EC2 instances grouped by lifecycle state (read-only)."""
        return ec2.instance_state_counts(session, region=region or None)
