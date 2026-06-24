"""Read-only Amazon S3 handlers.

Every function here is non-mutating: it only lists or describes resources. All
return values are plain, JSON-serializable dictionaries so they can be handed
straight back to an MCP client.
"""

from __future__ import annotations

from typing import Any

# Hard cap so a tool call can never page through an unbounded bucket and blow up
# the client. Callers can request fewer, never more.
MAX_KEYS_LIMIT = 1000


def list_buckets(session: Any) -> dict[str, Any]:
    """List all S3 buckets visible to the configured credentials."""
    client = session.client("s3")
    response = client.list_buckets()
    buckets = [
        {
            "name": bucket["Name"],
            "creation_date": _isoformat(bucket.get("CreationDate")),
        }
        for bucket in response.get("Buckets", [])
    ]
    return {"count": len(buckets), "buckets": buckets}


def list_objects(
    session: Any,
    bucket: str,
    prefix: str = "",
    max_keys: int = 100,
) -> dict[str, Any]:
    """List objects in a bucket, optionally filtered by key prefix.

    ``max_keys`` is clamped to ``[1, MAX_KEYS_LIMIT]`` to keep responses bounded.
    """
    max_keys = max(1, min(int(max_keys), MAX_KEYS_LIMIT))
    client = session.client("s3")
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=max_keys)
    objects = [
        {
            "key": obj["Key"],
            "size": obj.get("Size", 0),
            "last_modified": _isoformat(obj.get("LastModified")),
            "storage_class": obj.get("StorageClass", "STANDARD"),
        }
        for obj in response.get("Contents", [])
    ]
    return {
        "bucket": bucket,
        "prefix": prefix,
        "count": len(objects),
        "truncated": bool(response.get("IsTruncated", False)),
        "objects": objects,
    }


def bucket_summary(session: Any, bucket: str, max_keys: int = 1000) -> dict[str, Any]:
    """Summarize a bucket: object count and total size over the first page.

    This samples up to ``max_keys`` objects (a single API page) rather than
    walking the entire bucket, so it stays fast and cheap. ``sampled`` reports
    whether the bucket is larger than what was measured.
    """
    listing = list_objects(session, bucket, max_keys=max_keys)
    total_bytes = sum(obj["size"] for obj in listing["objects"])
    return {
        "bucket": bucket,
        "objects_measured": listing["count"],
        "total_bytes": total_bytes,
        "total_human": _human_bytes(total_bytes),
        "sampled": listing["truncated"],
    }


def _isoformat(value: Any) -> str | None:
    return value.isoformat() if hasattr(value, "isoformat") else value


def _human_bytes(num: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} EiB"
