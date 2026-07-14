"""Tests for the environment variable agent (phase 1)."""

import json

import pytest

from env_agent.agent import EnvAgent
from env_agent.errors import NotFoundError, ValidationError
from env_agent.models import EnvCommand, EnvState, EnvVariable, is_valid_variable_name
from env_agent.store import JsonStore


def _cmd(action, args=None, request_id=None):
    return EnvCommand(action=action, args=args or {}, request_id=request_id)


def test_is_valid_variable_name():
    assert is_valid_variable_name("FOO")
    assert is_valid_variable_name("_FOO1")
    assert not is_valid_variable_name("1FOO")
    assert not is_valid_variable_name("FOO-BAR")


def test_set_and_get_roundtrip():
    agent = EnvAgent()
    resp = agent.handle(_cmd("set", {"key": "GREETING", "value": "hello"}))
    assert resp.status == "ok"
    assert resp.data["created"] is True

    resp = agent.handle(_cmd("get", {"key": "GREETING"}))
    assert resp.status == "ok"
    assert resp.data["value"] == "hello"


def test_set_coerces_non_string_values_to_json():
    agent = EnvAgent()
    agent.handle(_cmd("set", {"key": "LIST", "value": [1, 2, 3]}))
    resp = agent.handle(_cmd("get", {"key": "LIST"}))
    assert json.loads(resp.data["value"]) == [1, 2, 3]


def test_get_missing_raises_not_found():
    agent = EnvAgent()
    resp = agent.handle(_cmd("get", {"key": "NOPE"}))
    assert resp.status == "error"
    assert resp.error["code"] == "not_found"


def test_invalid_key_name():
    agent = EnvAgent()
    resp = agent.handle(_cmd("set", {"key": "1BAD", "value": "x"}))
    assert resp.status == "error"
    assert resp.error["code"] == "validation_error"


def test_delete_and_has():
    agent = EnvAgent()
    agent.handle(_cmd("set", {"key": "TEMP", "value": "v"}))
    assert agent.handle(_cmd("has", {"key": "TEMP"})).data["exists"] is True
    assert agent.handle(_cmd("delete", {"key": "TEMP"})).data["deleted"] is True
    assert agent.handle(_cmd("has", {"key": "TEMP"})).data["exists"] is False


def test_list_masks_secrets():
    agent = EnvAgent()
    agent.handle(_cmd("set", {"key": "PUBLIC", "value": "open"}))
    agent.handle(_cmd("set", {"key": "PASSWORD", "value": "s3cret", "secret": True}))

    visible = agent.handle(_cmd("list", {"include_secrets": True}))
    assert visible.data["variables"]["PASSWORD"]["value"] == "s3cret"

    masked = agent.handle(_cmd("list", {"include_secrets": False}))
    assert masked.data["variables"]["PASSWORD"]["value"] == "********"
    assert masked.data["variables"]["PUBLIC"]["value"] == "open"


def test_export_excludes_secrets_when_masked():
    agent = EnvAgent()
    agent.handle(_cmd("set", {"key": "API_KEY", "value": "xyz", "secret": True}))
    agent.handle(_cmd("set", {"key": "MODE", "value": "prod"}))
    resp = agent.handle(_cmd("export", {"include_secrets": False}))
    assert "API_KEY" not in resp.data["variables"]
    assert resp.data["variables"]["MODE"] == "prod"


def test_unknown_action():
    agent = EnvAgent()
    resp = agent.handle(_cmd("frobnicate", {}))
    assert resp.status == "error"
    assert resp.error["code"] == "unknown_action"


def test_invalid_command_json_returns_error_response():
    agent = EnvAgent()
    raw = '{"action": "", "args": {}}'
    resp = json.loads(agent.handle_json(raw))
    assert resp["status"] == "error"


def test_load_and_dump_roundtrip_json():
    agent = EnvAgent()
    state = {
        "schema_version": 1,
        "phase": "phase-1",
        "variables": {
            "A": {"value": "1", "secret": False, "description": None, "updated_at": "x"}
        },
    }
    resp = agent.handle(_cmd("load", {"state": state}))
    assert resp.status == "ok"

    dumped = agent.handle(_cmd("dump", {}))
    assert dumped.data["variables"]["A"]["value"] == "1"


def test_handle_json_echoes_request_id():
    agent = EnvAgent()
    raw = json.dumps(
        {"action": "set", "args": {"key": "K", "value": "v"}, "request_id": "req-7"}
    )
    resp = json.loads(agent.handle_json(raw))
    assert resp["request_id"] == "req-7"


def test_json_store_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    store = JsonStore(path=str(path))
    agent = EnvAgent(store=store)
    agent.handle(_cmd("set", {"key": "PERSIST", "value": "keep"}))
    agent.handle(_cmd("save", {}))

    assert path.is_file()
    reloaded = EnvAgent(store=JsonStore(path=str(path)))
    reloaded.handle(_cmd("load", {}))
    assert reloaded.state.variables["PERSIST"].value == "keep"


def test_json_store_atomic_write_is_valid_json(tmp_path):
    path = tmp_path / "state.json"
    store = JsonStore(path=str(path))
    store.save(EnvState(variables={"X": EnvVariable(value="1")}))
    parsed = json.loads(path.read_text())
    assert parsed["variables"]["X"]["value"] == "1"
