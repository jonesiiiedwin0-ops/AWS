"""AWS MCP Server - Model Context Protocol server for AWS services integration."""

__version__ = "0.2.0"
__author__ = "jonesiiiedwin0-ops"
__license__ = "MIT"

from .config import Config
from .server import MCPServer

__all__ = ["MCPServer", "Config", "__version__"]
