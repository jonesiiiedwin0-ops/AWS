"""Read-only AWS Lambda handlers.

Non-mutating list/describe calls only. Return values are plain,
JSON-serializable dictionaries so they can be handed straight back to an MCP
client. The module is named ``lambda_`` because ``lambda`` is a reserved word.
"""

from __future__ import annotations

from typing import Any

# Hard cap so a single call can never page through an unbounded account and
# blow up the client. Callers can request fewer, never more.
MAX_FUNCTIONS_LIMIT = 1000


def list_functions(
    session: Any,
    region: str | None = None,
    max_functions: int = 100,
) -> dict[str, Any]:
    """List Lambda functions, one record per function.

    ``max_functions`` is clamped to ``[1, MAX_FUNCTIONS_LIMIT]`` to keep
    responses bounded. ``truncated`` reports whether more functions exist than
    were returned.
    """
    max_functions = max(1, min(int(max_functions), MAX_FUNCTIONS_LIMIT))
    client = session.client("lambda", region_name=region) if region else session.client("lambda")

    functions: list[dict[str, Any]] = []
    truncated = False
    paginator = client.get_paginator("list_functions")
    for page in paginator.paginate():
        for fn in page.get("Functions", []):
            functions.append(_function_record(fn))
            if len(functions) >= max_functions:
                truncated = True
                break
        if truncated:
            break

    return {
        "count": len(functions),
        "truncated": truncated,
        "functions": functions,
    }


def runtime_counts(session: Any, region: str | None = None) -> dict[str, Any]:
    """Aggregate function counts by runtime (python3.12, nodejs20.x, ...)."""
    listed = list_functions(session, region=region, max_functions=MAX_FUNCTIONS_LIMIT)
    counts: dict[str, int] = {}
    for fn in listed["functions"]:
        runtime = fn.get("runtime") or "unknown"
        counts[runtime] = counts.get(runtime, 0) + 1
    return {"total": listed["count"], "by_runtime": counts}


def _function_record(fn: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": fn.get("FunctionName"),
        "runtime": fn.get("Runtime"),
        "handler": fn.get("Handler"),
        "memory_mb": fn.get("MemorySize"),
        "timeout_s": fn.get("Timeout"),
        "code_size": fn.get("CodeSize"),
        "last_modified": fn.get("LastModified"),
        "description": fn.get("Description") or None,
    }
