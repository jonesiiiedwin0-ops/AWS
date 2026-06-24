"""RDS service integration."""

from typing import Any, Callable, Dict

from .base import BaseService


class RDSService(BaseService):
    """Relational Database Service operations."""

    service_name = "rds"
    display_name = "RDS"
    description = "Managed relational databases (MySQL, PostgreSQL, etc.)"

    def _build_tools(self) -> Dict[str, Callable]:
        return {
            "list_db_instances": self.list_db_instances,
            "describe_db_instance": self.describe_db_instance,
            "list_db_snapshots": self.list_db_snapshots,
        }

    async def list_db_instances(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List RDS database instances."""
        client = self.get_client(params.get("region"))
        response = client.describe_db_instances(
            MaxRecords=params.get("max_records", 100),
        )
        instances = [
            {
                "identifier": db.get("DBInstanceIdentifier"),
                "engine": db.get("Engine"),
                "engine_version": db.get("EngineVersion"),
                "status": db.get("DBInstanceStatus"),
                "instance_class": db.get("DBInstanceClass"),
                "storage_gb": db.get("AllocatedStorage"),
                "multi_az": db.get("MultiAZ"),
            }
            for db in response.get("DBInstances", [])
        ]
        return {"count": len(instances), "db_instances": instances}

    async def describe_db_instance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Describe a single DB instance."""
        client = self.get_client(params.get("region"))
        response = client.describe_db_instances(
            DBInstanceIdentifier=params["identifier"],
        )
        instances = response.get("DBInstances", [])
        if not instances:
            return {"found": False, "identifier": params["identifier"]}
        return {"found": True, "db_instance": instances[0]}

    async def list_db_snapshots(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List DB snapshots."""
        client = self.get_client(params.get("region"))
        kwargs: Dict[str, Any] = {"MaxRecords": params.get("max_records", 100)}
        if identifier := params.get("identifier"):
            kwargs["DBInstanceIdentifier"] = identifier
        response = client.describe_db_snapshots(**kwargs)
        snapshots = [
            {
                "snapshot_id": s.get("DBSnapshotIdentifier"),
                "instance_id": s.get("DBInstanceIdentifier"),
                "status": s.get("Status"),
                "created": str(s.get("SnapshotCreateTime")),
            }
            for s in response.get("DBSnapshots", [])
        ]
        return {"count": len(snapshots), "snapshots": snapshots}
