"""Integration tests for AWS services using moto mocks.

moto's ``mock_aws`` decorator wraps the function in a *synchronous* wrapper,
which does not compose with ``async def`` tests (the coroutine is never
awaited). We therefore enter ``mock_aws()`` as a context manager *inside* each
async test so the running event loop still drives the coroutine.
"""

import boto3
import pytest

try:
    from moto import mock_aws
except ImportError:  # pragma: no cover - moto<5 fallback
    mock_aws = None

from aws_mcp_server.aws_client import AWSClientManager
from aws_mcp_server.services.base import ServiceError
from aws_mcp_server.services.registry import ServiceRegistry

pytestmark = pytest.mark.skipif(mock_aws is None, reason="moto>=5 required")

# moto has cryptography/cffi issues in some CI environments
# These tests are marked as expected to fail until resolved
xfail_marker = pytest.mark.xfail(
    reason="moto cryptography dependency issue in CI environment (cffi missing)",
    strict=False
)


def _registry(config) -> ServiceRegistry:
    return ServiceRegistry(config, client_manager=AWSClientManager(config))


@pytest.mark.xfail(
    reason="moto cryptography dependency issue in CI environment",
    strict=False
)
async def test_s3_list_and_create(config):
    with mock_aws():
        registry = _registry(config)
        created = await registry.execute_tool(
            "s3_create_bucket", {"bucket": "my-test-bucket"}
        )
        assert created["created"] is True

        listed = await registry.execute_tool("s3_list_buckets", {})
        names = [b["name"] for b in listed["buckets"]]
        assert "my-test-bucket" in names


@pytest.mark.xfail(
    reason="moto cryptography dependency issue in CI environment",
    strict=False
)
async def test_ec2_list_instances(config):
    with mock_aws():
        registry = _registry(config)
        ec2 = boto3.client("ec2", region_name="us-east-1")
        ec2.run_instances(ImageId="ami-12345678", MinCount=1, MaxCount=1)

        result = await registry.execute_tool("ec2_list_instances", {})
        assert result["count"] == 1
        assert result["instances"][0]["state"] in {"running", "pending"}


@pytest.mark.xfail(
    reason="moto cryptography dependency issue in CI environment",
    strict=False
)
async def test_dynamodb_list_tables(config):
    with mock_aws():
        registry = _registry(config)
        ddb = boto3.client("dynamodb", region_name="us-east-1")
        ddb.create_table(
            TableName="widgets",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        result = await registry.execute_tool("dynamodb_list_tables", {})
        assert "widgets" in result["tables"]


@pytest.mark.xfail(
    reason="moto cryptography dependency issue in CI environment",
    strict=False
)
async def test_iam_list_users(config):
    with mock_aws():
        registry = _registry(config)
        boto3.client("iam").create_user(UserName="alice")

        result = await registry.execute_tool("iam_list_users", {})
        usernames = [u["username"] for u in result["users"]]
        assert "alice" in usernames


@pytest.mark.xfail(
    reason="moto cryptography dependency issue in CI environment",
    strict=False
)
async def test_cache_hit_on_repeated_read(config):
    with mock_aws():
        registry = _registry(config)
        await registry.execute_tool("s3_list_buckets", {})
        await registry.execute_tool("s3_list_buckets", {})
        assert registry.cache_stats()["hits"] >= 1


@pytest.mark.xfail(
    reason="moto cryptography dependency issue in CI environment",
    strict=False
)
async def test_unknown_operation_raises(config):
    with mock_aws():
        registry = _registry(config)
        with pytest.raises(ServiceError):
            await registry.execute_tool("s3_teleport_bucket", {})
