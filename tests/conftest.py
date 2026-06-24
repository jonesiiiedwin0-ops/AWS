"""Shared pytest fixtures."""

import pytest

from aws_mcp_server.config import Config


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    """Provide dummy AWS credentials so boto3/moto never touch real AWS."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def config() -> Config:
    """A test configuration with all services enabled."""
    return Config(
        aws_region="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        enabled_services=["ec2", "s3", "lambda", "dynamodb", "rds", "iam"],
        enable_rate_limiting=False,
    )
