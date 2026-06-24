"""Tests for configuration loading."""

import pytest

from aws_mcp_server.config import DEFAULT_REGION, DEFAULT_SERVICES, Config


def test_defaults_when_env_empty():
    cfg = Config.from_env({})
    assert cfg.region == DEFAULT_REGION
    assert cfg.read_only is True
    assert cfg.enabled_services == DEFAULT_SERVICES
    assert cfg.log_level == "INFO"


def test_reads_region_and_services():
    cfg = Config.from_env(
        {
            "AWS_REGION": "eu-west-1",
            "AWS_MCP_ENABLED_SERVICES": "s3, ec2 ,lambda",
        }
    )
    assert cfg.region == "eu-west-1"
    assert cfg.enabled_services == ("s3", "ec2", "lambda")


@pytest.mark.parametrize("value,expected", [("false", False), ("0", False), ("no", False)])
def test_read_only_can_be_disabled(value, expected):
    cfg = Config.from_env({"AWS_MCP_READ_ONLY": value})
    assert cfg.read_only is expected


@pytest.mark.parametrize("value", ["true", "1", "yes", "on"])
def test_read_only_truthy(value):
    cfg = Config.from_env({"AWS_MCP_READ_ONLY": value})
    assert cfg.read_only is True


def test_read_only_invalid_raises():
    with pytest.raises(ValueError):
        Config.from_env({"AWS_MCP_READ_ONLY": "maybe"})


def test_empty_services_falls_back_to_default():
    cfg = Config.from_env({"AWS_MCP_ENABLED_SERVICES": "  ,  "})
    assert cfg.enabled_services == DEFAULT_SERVICES


def test_log_level_uppercased():
    cfg = Config.from_env({"AWS_MCP_LOG_LEVEL": "debug"})
    assert cfg.log_level == "DEBUG"
