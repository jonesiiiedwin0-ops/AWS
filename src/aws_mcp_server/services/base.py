"""Base service class for AWS service integrations."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Raised when an AWS service operation fails."""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.code = code


class BaseService(ABC):
    """Abstract base class for AWS service integrations.

    Subclasses declare a ``service_name`` and register their operations in
    ``_build_tools``. The base class handles client acquisition and uniform
    error handling so concrete services stay focused on AWS logic.
    """

    #: AWS service name passed to boto3 (e.g. "ec2", "s3").
    service_name: str = ""
    #: Human-readable display name.
    display_name: str = ""
    #: Short description of the service.
    description: str = ""

    def __init__(self, client_manager: Any):
        """Initialize the service.

        Args:
            client_manager: An AWSClientManager instance.
        """
        self.client_manager = client_manager
        self._tools: Dict[str, Callable] = self._build_tools()

    @abstractmethod
    def _build_tools(self) -> Dict[str, Callable]:
        """Return a mapping of tool name -> async handler."""
        raise NotImplementedError

    def get_client(self, region: Optional[str] = None) -> Any:
        """Get a boto3 client for this service."""
        return self.client_manager.get_client(self.service_name, region)

    def list_tools(self) -> List[str]:
        """List the operations this service exposes."""
        return list(self._tools.keys())

    async def execute(self, tool: str, params: Dict[str, Any]) -> Any:
        """Execute a named tool with the given parameters.

        Args:
            tool: The operation name (without service prefix).
            params: Parameters for the operation.

        Returns:
            The operation result.

        Raises:
            ServiceError: If the tool is unknown or the AWS call fails.
        """
        handler = self._tools.get(tool)
        if handler is None:
            raise ServiceError(
                f"Unknown tool '{tool}' for service '{self.service_name}'",
                code="UnknownTool",
            )

        try:
            return await handler(params)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "ClientError")
            message = exc.response.get("Error", {}).get("Message", str(exc))
            logger.error("%s.%s failed: %s", self.service_name, tool, message)
            raise ServiceError(message, code=error_code) from exc
        except BotoCoreError as exc:
            logger.error("%s.%s boto error: %s", self.service_name, tool, exc)
            raise ServiceError(str(exc), code="BotoCoreError") from exc

    def metadata(self) -> Dict[str, Any]:
        """Return descriptive metadata for this service."""
        return {
            "name": self.display_name or self.service_name.upper(),
            "service": self.service_name,
            "description": self.description,
            "tools": self.list_tools(),
        }
