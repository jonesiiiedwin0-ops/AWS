"""Service registry that wires AWS services with caching, limits, and metrics."""

import logging
import time
from typing import Any, Dict, List, Optional

from ..aws_client import AWSClientManager
from ..cache import TTLCache
from ..config import Config
from ..metrics import MetricsCollector, default_collector
from ..rate_limiter import RateLimiter
from .base import ServiceError
from .dynamodb import DynamoDBService
from .ec2 import EC2Service
from .iam import IAMService
from .lambda_service import LambdaService
from .playwright_service import PlaywrightError, PlaywrightService
from .rds import RDSService
from .s3 import S3Service

logger = logging.getLogger(__name__)

# Operations whose results are safe to cache (read-only, idempotent).
_CACHEABLE_PREFIXES = ("list_", "describe_", "get_")

# All known service classes keyed by their service name.
_SERVICE_CLASSES = {
    "ec2": EC2Service,
    "s3": S3Service,
    "lambda": LambdaService,
    "dynamodb": DynamoDBService,
    "rds": RDSService,
    "iam": IAMService,
}

# Services that don't use AWS clients (lifecycle managed separately).
_NON_AWS_SERVICES = {
    "playwright": PlaywrightService,
}


class ServiceRegistry:
    """Registry for AWS services and their tools.

    Resolves ``<service>_<operation>`` tool names, applies rate limiting and
    caching, records metrics, and dispatches to the appropriate service.
    """

    def __init__(
        self,
        config: Config,
        client_manager: Optional[AWSClientManager] = None,
        cache: Optional[TTLCache] = None,
        rate_limiter: Optional[RateLimiter] = None,
        metrics: Optional[MetricsCollector] = None,
    ):
        """Initialize the registry.

        Args:
            config: Server configuration.
            client_manager: Optional AWS client manager (injected in tests).
            cache: Optional cache instance.
            rate_limiter: Optional rate limiter instance.
            metrics: Optional metrics collector.
        """
        self.config = config
        self.client_manager = client_manager or AWSClientManager(config)
        self.cache = cache or TTLCache(default_ttl=config.cache_ttl, max_size=1000)
        self.rate_limiter = rate_limiter or RateLimiter(
            rate=float(config.max_connections),
            capacity=config.max_connections * 2,
        )
        self.metrics = metrics or default_collector
        self.services: Dict[str, Any] = {}
        self._initialize_services()

    def _initialize_services(self) -> None:
        """Instantiate enabled services."""
        for name in self.config.enabled_services:
            if name in _NON_AWS_SERVICES:
                self.services[name] = _NON_AWS_SERVICES[name]()
                logger.info("Service %s initialized", name)
                continue

            service_cls = _SERVICE_CLASSES.get(name)
            if service_cls is None:
                logger.warning("Unknown service '%s' in enabled_services", name)
                continue
            self.services[name] = service_cls(self.client_manager)  # type: ignore[abstract]
            logger.info("Service %s initialized", name)

    def list_available_services(self) -> List[str]:
        """Get list of all initialized services."""
        return list(self.services.keys())

    def list_enabled_services(self) -> List[str]:
        """Get the configured enabled-services list."""
        return self.config.enabled_services

    def service_metadata(self) -> List[Dict[str, Any]]:
        """Return metadata for all initialized services."""
        return [svc.metadata() for svc in self.services.values()]

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return all tools across services as MCP-style descriptors."""
        tools: List[Dict[str, Any]] = []
        for name, svc in self.services.items():
            for tool in svc.list_tools():
                tools.append(
                    {
                        "name": f"{name}_{tool}",
                        "service": name,
                        "operation": tool,
                        "description": f"{svc.display_name}: {tool}",
                    }
                )
        return tools

    @staticmethod
    def _split_tool_name(tool_name: str) -> tuple[str, str]:
        """Split ``<service>_<operation>`` into its parts.

        Raises:
            ServiceError: If the name has no service prefix.
        """
        if "_" not in tool_name:
            raise ServiceError(
                f"Invalid tool name '{tool_name}'; expected '<service>_<operation>'",
                code="InvalidToolName",
            )
        service, operation = tool_name.split("_", 1)
        return service, operation

    def _is_cacheable(self, operation: str) -> bool:
        return self.config.enable_caching and operation.startswith(_CACHEABLE_PREFIXES)

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        client_id: str = "global",
    ) -> Any:
        """Execute a tool by name, applying limits, caching, and metrics.

        Args:
            tool_name: Tool in the form ``<service>_<operation>``.
            params: Parameters for the operation.
            client_id: Identifier used for rate limiting.

        Returns:
            The operation result.

        Raises:
            ServiceError: If the service/operation is unknown or AWS errors.
            RateLimitExceeded: If the caller is rate limited.
        """
        if self.config.enable_rate_limiting:
            self.rate_limiter.check(client_id)

        service_name, operation = self._split_tool_name(tool_name)
        service = self.services.get(service_name)
        if service is None:
            raise ServiceError(
                f"Service '{service_name}' is not enabled", code="ServiceNotEnabled"
            )

        cache_key = None
        if self._is_cacheable(operation):
            cache_key = f"{tool_name}:{sorted(params.items())}"
            cached = self.cache.get(cache_key)
            if cached is not None:
                self.metrics.inc_counter(
                    "aws_mcp_cache_hits_total", service=service_name
                )
                return cached

        start = time.monotonic()
        status = "success"
        try:
            result = await service.execute(operation, params)
            if cache_key is not None:
                self.cache.set(cache_key, result)
            return result
        except (PlaywrightError, ServiceError):
            status = "error"
            raise
        except Exception:
            status = "error"
            raise
        finally:
            elapsed = time.monotonic() - start
            self.metrics.inc_counter(
                "aws_mcp_tool_calls_total",
                service=service_name,
                operation=operation,
                status=status,
            )
            self.metrics.observe(
                "aws_mcp_tool_duration_seconds",
                elapsed,
                service=service_name,
            )

    def cache_stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        return self.cache.stats()
