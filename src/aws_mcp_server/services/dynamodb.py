"""DynamoDB service integration."""

from typing import Any, Callable, Dict

from .base import BaseService


class DynamoDBService(BaseService):
    """DynamoDB NoSQL database operations."""

    service_name = "dynamodb"
    display_name = "DynamoDB"
    description = "Fully managed NoSQL key-value and document database"

    def _build_tools(self) -> Dict[str, Callable]:
        return {
            "list_tables": self.list_tables,
            "describe_table": self.describe_table,
            "get_item": self.get_item,
            "query": self.query,
        }

    async def list_tables(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List DynamoDB tables."""
        client = self.get_client(params.get("region"))
        response = client.list_tables(Limit=params.get("limit", 100))
        return {
            "count": len(response.get("TableNames", [])),
            "tables": response.get("TableNames", []),
        }

    async def describe_table(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Describe a DynamoDB table."""
        client = self.get_client(params.get("region"))
        response = client.describe_table(TableName=params["table_name"])
        table = response.get("Table", {})
        return {
            "name": table.get("TableName"),
            "status": table.get("TableStatus"),
            "item_count": table.get("ItemCount"),
            "size_bytes": table.get("TableSizeBytes"),
            "key_schema": table.get("KeySchema", []),
        }

    async def get_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a single item by key."""
        client = self.get_client(params.get("region"))
        response = client.get_item(
            TableName=params["table_name"],
            Key=params["key"],
        )
        return {"found": "Item" in response, "item": response.get("Item")}

    async def query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query a table using a key condition expression."""
        client = self.get_client(params.get("region"))
        query_kwargs: Dict[str, Any] = {
            "TableName": params["table_name"],
            "KeyConditionExpression": params["key_condition_expression"],
            "Limit": params.get("limit", 100),
        }
        if values := params.get("expression_attribute_values"):
            query_kwargs["ExpressionAttributeValues"] = values
        response = client.query(**query_kwargs)
        return {
            "count": response.get("Count", 0),
            "items": response.get("Items", []),
        }
