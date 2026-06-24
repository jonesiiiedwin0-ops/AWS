"""Tests for the MCP Server."""

import pytest
from aws_mcp_server import MCPServer
from aws_mcp_server.config import Config


class TestMCPServer:
    """Tests for MCPServer class."""

    def test_server_initialization(self):
        """Test server initialization."""
        server = MCPServer()
        assert server is not None
        assert server.config is not None

    def test_server_with_custom_config(self):
        """Test server initialization with custom config."""
        config = Config(server_port=9000, aws_region="us-west-2")
        server = MCPServer(config)
        assert server.config.server_port == 9000
        assert server.config.aws_region == "us-west-2"

    def test_service_registry_initialization(self):
        """Test service registry is initialized."""
        server = MCPServer()
        assert server.service_registry is not None

    def test_list_available_services(self):
        """Test listing available services."""
        server = MCPServer()
        services = server.service_registry.list_available_services()
        assert isinstance(services, list)
        assert len(services) > 0
