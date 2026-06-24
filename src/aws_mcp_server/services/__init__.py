"""Read-only AWS service handlers.

Each module exposes plain functions that take a ``boto3.Session`` and return
JSON-serializable dictionaries. Keeping the AWS calls behind small, pure
functions makes them trivial to unit-test with ``moto`` — no live account
required — and keeps the MCP wiring in :mod:`aws_mcp_server.server` thin.
"""

from __future__ import annotations

__all__ = ["s3", "ec2", "lambda_"]
