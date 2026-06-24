"""Tests for the command-line entry point."""

import pytest

from aws_mcp_server import __version__
from aws_mcp_server.__main__ import build_parser, main


def test_version_flag_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_check_mode_returns_zero(monkeypatch, capsys):
    monkeypatch.delenv("AWS_MCP_READ_ONLY", raising=False)
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    rc = main(["--check"])
    assert rc == 0
    assert "Configuration OK" in capsys.readouterr().out


def test_run_without_transport_returns_two(capsys):
    rc = main([])
    assert rc == 2
    assert "not implemented yet" in capsys.readouterr().err
