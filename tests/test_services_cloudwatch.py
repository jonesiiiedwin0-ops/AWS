"""Tests for the read-only CloudWatch handlers, backed by moto (no live AWS)."""

import boto3
import pytest
from moto import mock_aws

from aws_mcp_server.services import cloudwatch

REGION = "us-east-1"


@pytest.fixture
def session():
    with mock_aws():
        yield boto3.Session(region_name=REGION)


def _put_alarm(session, name, state="OK", metric="CPUUtilization"):
    client = session.client("cloudwatch")
    client.put_metric_alarm(
        AlarmName=name,
        AlarmDescription=f"{name} desc",
        Namespace="AWS/EC2",
        MetricName=metric,
        Statistic="Average",
        Period=300,
        EvaluationPeriods=1,
        Threshold=80.0,
        ComparisonOperator="GreaterThanThreshold",
        ActionsEnabled=True,
    )
    # moto honors an explicit state set via set_alarm_state.
    client.set_alarm_state(
        AlarmName=name, StateValue=state, StateReason="test"
    )


def test_list_alarms_empty(session):
    result = cloudwatch.list_alarms(session)
    assert result == {"count": 0, "truncated": False, "alarms": []}


def test_list_alarms_returns_records(session):
    _put_alarm(session, "cpu-high")
    result = cloudwatch.list_alarms(session)
    assert result["count"] == 1
    alarm = result["alarms"][0]
    assert alarm["name"] == "cpu-high"
    assert alarm["metric"] == "CPUUtilization"
    assert alarm["namespace"] == "AWS/EC2"
    assert alarm["comparison"] == "GreaterThanThreshold"
    assert alarm["threshold"] == 80.0
    assert alarm["description"] == "cpu-high desc"


def test_list_alarms_clamps_and_truncates(session):
    for i in range(5):
        _put_alarm(session, f"alarm{i}")
    result = cloudwatch.list_alarms(session, max_alarms=2)
    assert result["count"] == 2
    assert result["truncated"] is True
    # Over the hard limit clamps down rather than raising.
    assert cloudwatch.list_alarms(session, max_alarms=10_000)["count"] == 5


def test_list_alarms_filters_by_state(session):
    _put_alarm(session, "ok-1", state="OK")
    _put_alarm(session, "fire-1", state="ALARM")
    result = cloudwatch.list_alarms(session, state="alarm")
    assert result["count"] == 1
    assert result["alarms"][0]["name"] == "fire-1"


def test_list_alarms_rejects_unknown_state(session):
    with pytest.raises(ValueError):
        cloudwatch.list_alarms(session, state="bogus")


def test_alarm_state_counts(session):
    _put_alarm(session, "ok-1", state="OK")
    _put_alarm(session, "ok-2", state="OK")
    _put_alarm(session, "fire-1", state="ALARM")
    result = cloudwatch.alarm_state_counts(session)
    assert result["total"] == 3
    assert result["by_state"] == {"OK": 2, "ALARM": 1, "INSUFFICIENT_DATA": 0}
