"""Read-only Amazon CloudWatch handlers.

Non-mutating describe/list calls only. Return values are plain,
JSON-serializable dictionaries so they can be handed straight back to an MCP
client. The first slice covers metric alarms — the thing people most often ask
an AI about ("what's on fire right now?").
"""

from __future__ import annotations

from typing import Any

# Hard cap so a single call can never page through an unbounded account and
# blow up the client. Callers can request fewer, never more.
MAX_ALARMS_LIMIT = 1000

# The states a CloudWatch metric alarm can report. We seed counts with these so
# state-count responses always have a stable shape, even for an empty account.
ALARM_STATES = ("OK", "ALARM", "INSUFFICIENT_DATA")


def list_alarms(
    session: Any,
    region: str | None = None,
    state: str | None = None,
    max_alarms: int = 100,
) -> dict[str, Any]:
    """List CloudWatch metric alarms, one record per alarm.

    ``state`` optionally filters to a single alarm state (``OK``, ``ALARM``, or
    ``INSUFFICIENT_DATA``). ``max_alarms`` is clamped to
    ``[1, MAX_ALARMS_LIMIT]`` to keep responses bounded; ``truncated`` reports
    whether more alarms exist than were returned.
    """
    max_alarms = max(1, min(int(max_alarms), MAX_ALARMS_LIMIT))
    client = (
        session.client("cloudwatch", region_name=region)
        if region
        else session.client("cloudwatch")
    )

    kwargs: dict[str, Any] = {}
    if state:
        normalized = state.strip().upper()
        if normalized not in ALARM_STATES:
            raise ValueError(
                f"state must be one of {ALARM_STATES}, got {state!r}"
            )
        kwargs["StateValue"] = normalized

    alarms: list[dict[str, Any]] = []
    truncated = False
    paginator = client.get_paginator("describe_alarms")
    for page in paginator.paginate(**kwargs):
        for alarm in page.get("MetricAlarms", []):
            alarms.append(_alarm_record(alarm))
            if len(alarms) >= max_alarms:
                truncated = True
                break
        if truncated:
            break

    return {
        "count": len(alarms),
        "truncated": truncated,
        "alarms": alarms,
    }


def alarm_state_counts(session: Any, region: str | None = None) -> dict[str, Any]:
    """Aggregate alarm counts by state (OK, ALARM, INSUFFICIENT_DATA).

    Counts are seeded at zero for every known state so the response shape is
    stable regardless of what the account currently holds.
    """
    listed = list_alarms(session, region=region, max_alarms=MAX_ALARMS_LIMIT)
    counts: dict[str, int] = dict.fromkeys(ALARM_STATES, 0)
    for alarm in listed["alarms"]:
        state = alarm.get("state") or "INSUFFICIENT_DATA"
        counts[state] = counts.get(state, 0) + 1
    return {"total": listed["count"], "by_state": counts}


def _alarm_record(alarm: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": alarm.get("AlarmName"),
        "state": alarm.get("StateValue"),
        "metric": alarm.get("MetricName"),
        "namespace": alarm.get("Namespace"),
        "comparison": alarm.get("ComparisonOperator"),
        "threshold": alarm.get("Threshold"),
        "actions_enabled": alarm.get("ActionsEnabled"),
        "description": alarm.get("AlarmDescription") or None,
    }
