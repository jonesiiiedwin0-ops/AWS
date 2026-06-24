"""Lambda service integration."""

import json
from typing import Any, Callable, Dict

from .base import BaseService


class LambdaService(BaseService):
    """AWS Lambda function operations."""

    service_name = "lambda"
    display_name = "Lambda"
    description = "AWS Lambda - run code without provisioning servers"

    def _build_tools(self) -> Dict[str, Callable]:
        return {
            "list_functions": self.list_functions,
            "get_function": self.get_function,
            "invoke_function": self.invoke_function,
            "list_aliases": self.list_aliases,
        }

    async def list_functions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Lambda functions."""
        client = self.get_client(params.get("region"))
        response = client.list_functions(MaxItems=params.get("max_items", 50))
        functions = [
            {
                "name": f.get("FunctionName"),
                "runtime": f.get("Runtime"),
                "memory": f.get("MemorySize"),
                "timeout": f.get("Timeout"),
                "last_modified": f.get("LastModified"),
                "handler": f.get("Handler"),
            }
            for f in response.get("Functions", [])
        ]
        return {"count": len(functions), "functions": functions}

    async def get_function(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get configuration for a single function."""
        client = self.get_client(params.get("region"))
        response = client.get_function(FunctionName=params["function_name"])
        config = response.get("Configuration", {})
        return {
            "name": config.get("FunctionName"),
            "arn": config.get("FunctionArn"),
            "runtime": config.get("Runtime"),
            "handler": config.get("Handler"),
            "memory": config.get("MemorySize"),
            "timeout": config.get("Timeout"),
            "state": config.get("State"),
        }

    async def invoke_function(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a Lambda function synchronously or asynchronously."""
        client = self.get_client(params.get("region"))
        payload = params.get("payload", {})
        response = client.invoke(
            FunctionName=params["function_name"],
            InvocationType=params.get("invocation_type", "RequestResponse"),
            Payload=json.dumps(payload).encode("utf-8"),
        )

        result: Dict[str, Any] = {
            "status_code": response.get("StatusCode"),
            "function_error": response.get("FunctionError"),
        }
        body = response.get("Payload")
        if body is not None:
            raw = body.read()
            try:
                result["response"] = json.loads(raw) if raw else None
            except (ValueError, TypeError):
                result["response"] = raw.decode("utf-8", errors="replace")
        return result

    async def list_aliases(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List aliases for a function."""
        client = self.get_client(params.get("region"))
        response = client.list_aliases(FunctionName=params["function_name"])
        aliases = [
            {"name": a.get("Name"), "version": a.get("FunctionVersion")}
            for a in response.get("Aliases", [])
        ]
        return {"count": len(aliases), "aliases": aliases}
