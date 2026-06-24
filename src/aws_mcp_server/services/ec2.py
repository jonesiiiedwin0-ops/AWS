"""Read-only Amazon EC2 handlers.

Non-mutating describe calls only. Return values are plain, JSON-serializable
dictionaries.
"""

from __future__ import annotations

from typing import Any


def describe_instances(session: Any, region: str | None = None) -> dict[str, Any]:
    """Describe EC2 instances, flattened to one record per instance."""
    client = session.client("ec2", region_name=region) if region else session.client("ec2")
    response = client.describe_instances()
    instances: list[dict[str, Any]] = []
    for reservation in response.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            instances.append(
                {
                    "id": inst.get("InstanceId"),
                    "type": inst.get("InstanceType"),
                    "state": inst.get("State", {}).get("Name"),
                    "availability_zone": inst.get("Placement", {}).get("AvailabilityZone"),
                    "private_ip": inst.get("PrivateIpAddress"),
                    "public_ip": inst.get("PublicIpAddress"),
                    "launch_time": _isoformat(inst.get("LaunchTime")),
                    "tags": {t["Key"]: t["Value"] for t in inst.get("Tags", [])},
                }
            )
    return {"count": len(instances), "instances": instances}


def instance_state_counts(session: Any, region: str | None = None) -> dict[str, Any]:
    """Aggregate instance counts by lifecycle state (running, stopped, ...)."""
    described = describe_instances(session, region=region)
    counts: dict[str, int] = {}
    for inst in described["instances"]:
        state = inst.get("state") or "unknown"
        counts[state] = counts.get(state, 0) + 1
    return {"total": described["count"], "by_state": counts}


def _isoformat(value: Any) -> str | None:
    return value.isoformat() if hasattr(value, "isoformat") else value
