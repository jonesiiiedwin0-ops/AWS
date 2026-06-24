"""DynamoDB service integration (read-only)."""

from typing import Any, Callable, Dict, List

from .base import BaseService


class DynamoDBService(BaseService):
    """DynamoDB NoSQL database operations (read-only)."""

    service_name = "dynamodb"
    display_name = "DynamoDB"
    description = "Fully managed NoSQL key-value and document database (read-only access)"

    def _build_tools(self) -> Dict[str, Callable]:
        return {
            "list_tables": self.list_tables,
            "describe_table": self.describe_table,
            "table_info": self.table_info,
        }

    async def list_tables(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all DynamoDB tables in the region."""
        client = self.get_client(params.get("region"))

        all_tables: List[str] = []
        exclusive_start_table_name = None

        while True:
            kwargs = {"Limit": 100}
            if exclusive_start_table_name:
                kwargs["ExclusiveStartTableName"] = exclusive_start_table_name

            response = client.list_tables(**kwargs)
            all_tables.extend(response.get("TableNames", []))

            if "LastEvaluatedTableName" not in response:
                break
            exclusive_start_table_name = response["LastEvaluatedTableName"]

        return {
            "count": len(all_tables),
            "tables": all_tables,
            "region": params.get("region", "default"),
        }

    async def describe_table(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Describe a single DynamoDB table."""
        client = self.get_client(params.get("region"))
        response = client.describe_table(TableName=params["table_name"])
        table = response.get("Table", {})
        return {
            "name": table.get("TableName"),
            "status": table.get("TableStatus"),
            "item_count": table.get("ItemCount", 0),
            "size_bytes": table.get("TableSizeBytes", 0),
            "key_schema": table.get("KeySchema", []),
            "attributes": table.get("AttributeDefinitions", []),
            "throughput": table.get("BillingModeSummary", table.get("ProvisionedThroughput", {})),
        }

    async def table_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive table information and statistics."""
        client = self.get_client(params.get("region"))
        response = client.describe_table(TableName=params["table_name"])
        table = response.get("Table", {})

        global_secondary_indexes = []
        for gsi in table.get("GlobalSecondaryIndexes", []):
            global_secondary_indexes.append({
                "name": gsi.get("IndexName"),
                "status": gsi.get("IndexStatus"),
                "key_schema": gsi.get("KeySchema", []),
                "provisioned_throughput": gsi.get("ProvisionedThroughput", gsi.get("BillingModeSummary", {})),
            })

        return {
            "table_name": table.get("TableName"),
            "arn": table.get("TableArn"),
            "status": table.get("TableStatus"),
            "creation_time": str(table.get("CreationDateTime", "")),
            "item_count": table.get("ItemCount", 0),
            "size_bytes": table.get("TableSizeBytes", 0),
            "billing_mode": table.get("BillingModeSummary", {}).get("BillingMode", "PROVISIONED"),
            "key_schema": table.get("KeySchema", []),
            "attributes": table.get("AttributeDefinitions", []),
            "global_secondary_indexes": global_secondary_indexes,
            "stream_specification": table.get("StreamSpecification", {}),
            "ttl": table.get("TimeToLiveDescription", {}),
        }
