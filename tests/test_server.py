"""Tests for the MCP Server and HTTP API."""

import pytest
from fastapi.testclient import TestClient

from aws_mcp_server import MCPServer
from aws_mcp_server.config import Config


@pytest.fixture
def client(config) -> TestClient:
    """A FastAPI TestClient wrapping a configured server."""
    server = MCPServer(config)
    return TestClient(server.app)


class TestMCPServer:
    """Tests for MCPServer construction."""

    def test_server_initialization(self, config):
        server = MCPServer(config)
        assert server is not None
        assert server.config is not None

    def test_server_with_custom_config(self):
        config = Config(server_port=9000, aws_region="us-west-2")
        server = MCPServer(config)
        assert server.config.server_port == 9000
        assert server.config.aws_region == "us-west-2"

    def test_service_registry_initialized(self, config):
        server = MCPServer(config)
        assert server.service_registry is not None
        assert len(server.service_registry.list_available_services()) == 6


class TestHTTPEndpoints:
    """Tests for the HTTP API surface."""

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert "ec2" in body["services"]

    def test_services(self, client):
        resp = client.get("/services")
        assert resp.status_code == 200
        assert "s3" in resp.json()["available_services"]

    def test_tools_listing(self, client):
        resp = client.get("/tools")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] > 0
        names = {t["name"] for t in body["tools"]}
        assert "ec2_list_instances" in names
        assert "s3_list_buckets" in names

    def test_metrics_endpoint(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "aws_mcp_uptime_seconds" in resp.text

    def test_execute_unknown_service(self, client):
        resp = client.post(
            "/execute",
            json={"tool_name": "fake_do_thing", "params": {}},
        )
        assert resp.status_code == 400

    def test_openapi_schema(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert schema["info"]["title"] == "AWS MCP Server"
        assert "/execute" in schema["paths"]
