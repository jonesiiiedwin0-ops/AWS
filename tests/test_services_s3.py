"""Tests for the read-only S3 handlers, backed by moto (no live AWS)."""

import boto3
import pytest
from moto import mock_aws

from aws_mcp_server.services import s3

REGION = "us-east-1"


@pytest.fixture
def session():
    with mock_aws():
        yield boto3.Session(region_name=REGION)


def _seed(session, bucket, items):
    client = session.client("s3")
    client.create_bucket(Bucket=bucket)
    for key, body in items:
        client.put_object(Bucket=bucket, Key=key, Body=body)


def test_list_buckets_empty(session):
    result = s3.list_buckets(session)
    assert result == {"count": 0, "buckets": []}


def test_list_buckets_returns_names(session):
    session.client("s3").create_bucket(Bucket="alpha")
    session.client("s3").create_bucket(Bucket="beta")
    result = s3.list_buckets(session)
    assert result["count"] == 2
    assert {b["name"] for b in result["buckets"]} == {"alpha", "beta"}


def test_list_objects_with_prefix(session):
    _seed(session, "data", [("logs/a.txt", b"x"), ("logs/b.txt", b"yy"), ("img/c.png", b"zzz")])
    result = s3.list_objects(session, "data", prefix="logs/")
    assert result["count"] == 2
    assert all(o["key"].startswith("logs/") for o in result["objects"])


def test_list_objects_clamps_max_keys(session):
    _seed(session, "data", [(f"k{i}", b"x") for i in range(5)])
    # Over the hard limit clamps down; zero/negative clamps up to 1.
    assert s3.list_objects(session, "data", max_keys=10_000)["count"] == 5
    assert s3.list_objects(session, "data", max_keys=0)["count"] == 1


def test_bucket_summary_totals_bytes(session):
    _seed(session, "data", [("a", b"123"), ("b", b"45")])
    summary = s3.bucket_summary(session, "data")
    assert summary["objects_measured"] == 2
    assert summary["total_bytes"] == 5
    assert summary["total_human"].endswith("B")
    assert summary["sampled"] is False
