"""Core MCP Server implementation for AWS services."""

import logging
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException
from .config import Config
from .services import ServiceRegistry
from .middleware import ErrorHandlerMiddleware, LoggingMiddleware

logger = logging.getLogger(__name__)


class MCPServer:
    """Main MCP Server class for AWS services integration."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the MCP Server."""
        self.config = config or Config()
        self.app = FastAPI(
            title="AWS MCP Server",
            description="Model Context Protocol server for AWS services",
            version="0.1.0",
        )
        self.service_registry = ServiceRegistry(self.config)

        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Configure middleware."""
        self.app.add_middleware(ErrorHandlerMiddleware)
        self.app.add_middleware(LoggingMiddleware)

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""

        @self.app.get("/health")
        async def health_check() -> Dict[str, Any]:
            """Health check endpoint."""
            return {
                "status": "healthy",
                "services": self.service_registry.list_available_services(),
                "version": "0.1.0",
            }

        @self.app.get("/services")
        async def list_services() -> Dict[str, List[str]]:
            """List available AWS services."""
            return {
                "available_services": self.service_registry.list_available_services(),
                "enabled_services": self.service_registry.list_enabled_services(),
            }

        @self.app.post("/execute")
        async def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict:
            """Execute an AWS service tool."""
            try:
                result = await self.service_registry.execute_tool(tool_name, params)
                return {
                    "status": "success",
                    "result": result,
                }
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                raise HTTPException(status_code=400, detail=str(e))

    async def start(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Start the server."""
        import uvicorn

        logger.info(f"Starting server on {host}:{port}")
        await uvicorn.run(self.app, host=host, port=port)
