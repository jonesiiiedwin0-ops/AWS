"""Service registry for AWS services."""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Registry for AWS services and their tools."""

    def __init__(self, config):
        """Initialize service registry."""
        self.config = config
        self.services: Dict[str, Dict[str, Any]] = {}
        self.tools: Dict[str, any] = {}
        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize available AWS services."""
        services = {
            "ec2": {"name": "EC2", "description": "Elastic Compute Cloud"},
            "s3": {"name": "S3", "description": "Simple Storage Service"},
            "lambda": {"name": "Lambda", "description": "AWS Lambda Functions"},
            "dynamodb": {"name": "DynamoDB", "description": "NoSQL Database Service"},
            "rds": {"name": "RDS", "description": "Relational Database Service"},
            "iam": {"name": "IAM", "description": "Identity and Access Management"},
        }

        for name, service in services.items():
            if name in self.config.enabled_services:
                self.services[name] = service
                logger.info(f"Service {name} initialized")

    def list_available_services(self) -> List[str]:
        """Get list of all available services."""
        return list(self.services.keys())

    def list_enabled_services(self) -> List[str]:
        """Get list of enabled services."""
        return self.config.enabled_services

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool."""
        logger.info(f"Executing tool: {tool_name}")
        return {
            "status": "success",
            "tool": tool_name,
            "message": f"Tool {tool_name} executed successfully",
        }
