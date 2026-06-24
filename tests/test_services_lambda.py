"""Tests for the read-only Lambda handlers, backed by moto (no live AWS)."""

import io
import json
import zipfile

import boto3
import pytest
from moto import mock_aws

from aws_mcp_server.services import lambda_

REGION = "us-east-1"

_ASSUME_ROLE_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ],
}


@pytest.fixture
def session():
    with mock_aws():
        sess = boto3.Session(region_name=REGION)
        # Newer moto validates that the execution role exists and is assumable
        # by Lambda, so create a real mock role for tests to reference.
        sess.client("iam").create_role(
            RoleName="lambda-role",
            AssumeRolePolicyDocument=json.dumps(_ASSUME_ROLE_POLICY),
        )
        yield sess


def _role_arn(session) -> str:
    return session.client("iam").get_role(RoleName="lambda-role")["Role"]["Arn"]


def _zip_bytes() -> bytes:
    """Minimal valid deployment package moto will accept."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("handler.py", "def handler(event, context):\n    return 'ok'\n")
    return buf.getvalue()


def _create(session, name, runtime="python3.12"):
    client = session.client("lambda")
    client.create_function(
        FunctionName=name,
        Runtime=runtime,
        Role=_role_arn(session),
        Handler="handler.handler",
        Code={"ZipFile": _zip_bytes()},
        Description=f"{name} fn",
    )


def test_list_functions_empty(session):
    result = lambda_.list_functions(session)
    assert result == {"count": 0, "truncated": False, "functions": []}


def test_list_functions_returns_records(session):
    _create(session, "alpha")
    _create(session, "beta", runtime="nodejs20.x")
    result = lambda_.list_functions(session)
    assert result["count"] == 2
    names = {f["name"] for f in result["functions"]}
    assert names == {"alpha", "beta"}
    alpha = next(f for f in result["functions"] if f["name"] == "alpha")
    assert alpha["runtime"] == "python3.12"
    assert alpha["handler"] == "handler.handler"
    assert alpha["description"] == "alpha fn"


def test_list_functions_clamps_and_truncates(session):
    for i in range(5):
        _create(session, f"fn{i}")
    result = lambda_.list_functions(session, max_functions=2)
    assert result["count"] == 2
    assert result["truncated"] is True
    # Over the hard limit clamps down rather than raising.
    assert lambda_.list_functions(session, max_functions=10_000)["count"] == 5


def test_runtime_counts(session):
    _create(session, "py1")
    _create(session, "py2")
    _create(session, "node1", runtime="nodejs20.x")
    result = lambda_.runtime_counts(session)
    assert result["total"] == 3
    assert result["by_runtime"] == {"python3.12": 2, "nodejs20.x": 1}
