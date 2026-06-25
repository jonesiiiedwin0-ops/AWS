"""Core MCP Server implementation for AWS services."""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

from .config import Config
from .metrics import MetricsCollector, default_collector
from .models import (
    ErrorResponse,
    ExecuteRequest,
    ExecuteResponse,
    HealthResponse,
    ServicesResponse,
    ToolDescriptor,
    ToolsResponse,
)
from .rate_limiter import RateLimitExceeded
from .services import ServiceRegistry
from .services.base import ServiceError
from .services.playwright_service import PlaywrightError
from .middleware import ErrorHandlerMiddleware, LoggingMiddleware

logger = logging.getLogger(__name__)

API_DESCRIPTION = """
The **AWS MCP Server** exposes AWS services through a standardized HTTP and
Model Context Protocol interface.

* **Health & discovery** — inspect server status and available tools.
* **Tool execution** — call AWS operations via a uniform `/execute` endpoint.
* **Observability** — Prometheus metrics at `/metrics`.

Tools are named `<service>_<operation>`, e.g. `ec2_list_instances`.
"""

OPENAPI_TAGS = [
    {"name": "health", "description": "Health checks and service discovery."},
    {"name": "tools", "description": "List and execute AWS service tools."},
    {"name": "observability", "description": "Metrics and cache statistics."},
]


class MCPServer:
    """Main MCP Server for AWS services integration."""

    def __init__(
        self,
        config: Optional[Config] = None,
        metrics: Optional[MetricsCollector] = None,
    ):
        """Initialize the MCP Server.

        Args:
            config: Server configuration. If None, loads from environment.
            metrics: Optional metrics collector (shared in tests).
        """
        self.config = config or Config()
        self.metrics = metrics or default_collector
        self.app = FastAPI(
            title="AWS MCP Server",
            description=API_DESCRIPTION,
            version="0.2.0",
            openapi_tags=OPENAPI_TAGS,
            contact={
                "name": "jonesiiiedwin0-ops",
                "url": "https://github.com/jonesiiiedwin0-ops/aws",
            },
            license_info={"name": "MIT"},
        )
        self.service_registry = ServiceRegistry(self.config, metrics=self.metrics)

        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Configure middleware."""
        self.app.add_middleware(ErrorHandlerMiddleware)
        self.app.add_middleware(LoggingMiddleware)

    @staticmethod
    def _client_id(request: Request) -> str:
        """Derive a rate-limit key from the request."""
        if request.client and request.client.host:
            return request.client.host
        return "global"

    def _setup_routes(self) -> None:
        """Register API routes."""
        app = self.app

        @app.get("/health", response_model=HealthResponse, tags=["health"])
        async def health_check() -> HealthResponse:
            """Return server health and initialized services."""
            return HealthResponse(
                status="healthy",
                services=self.service_registry.list_available_services(),
                version="0.2.0",
                credentials_valid=None,
            )

        @app.get("/services", response_model=ServicesResponse, tags=["health"])
        async def list_services() -> ServicesResponse:
            """List available and enabled AWS services."""
            return ServicesResponse(
                available_services=self.service_registry.list_available_services(),
                enabled_services=self.service_registry.list_enabled_services(),
            )

        @app.get("/tools", response_model=ToolsResponse, tags=["tools"])
        async def list_tools() -> ToolsResponse:
            """List every available tool across enabled services."""
            tools = self.service_registry.get_available_tools()
            return ToolsResponse(
                count=len(tools),
                tools=[ToolDescriptor(**t) for t in tools],
            )

        @app.post(
            "/execute",
            response_model=ExecuteResponse,
            tags=["tools"],
            responses={
                400: {"model": ErrorResponse},
                429: {"model": ErrorResponse},
            },
        )
        async def execute_tool(
            body: ExecuteRequest, request: Request
        ) -> ExecuteResponse:
            """Execute an AWS service tool with the given parameters."""
            try:
                result = await self.service_registry.execute_tool(
                    body.tool_name,
                    body.params,
                    client_id=self._client_id(request),
                )
                return ExecuteResponse(
                    status="success",
                    tool_name=body.tool_name,
                    result=result,
                    error=None,
                )
            except RateLimitExceeded as exc:
                raise HTTPException(
                    status_code=429,
                    detail=str(exc),
                    headers={"Retry-After": str(int(exc.retry_after) + 1)},
                )
            except (ServiceError, PlaywrightError) as exc:
                logger.warning("Tool %s failed: %s", body.tool_name, exc)
                raise HTTPException(status_code=400, detail=str(exc))

        @app.get("/metrics", response_class=PlainTextResponse, tags=["observability"])
        async def metrics() -> str:
            """Expose metrics in Prometheus text exposition format."""
            return self.metrics.render()

        @app.get("/cache/stats", tags=["observability"])
        async def cache_stats() -> Dict[str, Any]:
            """Return cache hit/miss statistics."""
            return self.service_registry.cache_stats()

    async def start(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Start the server with uvicorn."""
        import uvicorn

        logger.info("Starting server on %s:%s", host, port)
        server_config = uvicorn.Config(
            self.app, host=host, port=port, log_level=self.config.log_level.lower()
        )
        await uvicorn.Server(server_config).serve()
