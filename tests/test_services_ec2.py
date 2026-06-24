"""Tests for the read-only EC2 handlers, backed by moto (no live AWS)."""

import boto3
import pytest
from moto import mock_aws

from aws_mcp_server.services import ec2

REGION = "us-east-1"
# Canonical Amazon Linux AMI that moto recognizes.
AMI = "ami-12c6146b"


@pytest.fixture
def session():
    with mock_aws():
        yield boto3.Session(region_name=REGION)


def test_describe_instances_empty(session):
    result = ec2.describe_instances(session)
    assert result == {"count": 0, "instances": []}


def test_describe_instances_flattens_records(session):
    client = session.client("ec2", region_name=REGION)
    client.run_instances(ImageId=AMI, MinCount=2, MaxCount=2, InstanceType="t2.micro")
    result = ec2.describe_instances(session, region=REGION)
    assert result["count"] == 2
    inst = result["instances"][0]
    assert inst["type"] == "t2.micro"
    assert inst["state"] in {"running", "pending"}
    assert inst["id"].startswith("i-")


def test_instance_state_counts(session):
    client = session.client("ec2", region_name=REGION)
    client.run_instances(ImageId=AMI, MinCount=3, MaxCount=3, InstanceType="t2.micro")
    counts = ec2.instance_state_counts(session, region=REGION)
    assert counts["total"] == 3
    assert sum(counts["by_state"].values()) == 3
