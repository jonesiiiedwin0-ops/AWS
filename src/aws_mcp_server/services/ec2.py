"""EC2 service integration."""

from typing import Any, Callable, Dict, List

from .base import BaseService


class EC2Service(BaseService):
    """Elastic Compute Cloud operations."""

    service_name = "ec2"
    display_name = "EC2"
    description = "Elastic Compute Cloud - virtual servers in the cloud"

    def _build_tools(self) -> Dict[str, Callable]:
        return {
            "list_instances": self.list_instances,
            "describe_instance": self.describe_instance,
            "start_instance": self.start_instance,
            "stop_instance": self.stop_instance,
            "list_security_groups": self.list_security_groups,
            "list_volumes": self.list_volumes,
        }

    async def list_instances(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List EC2 instances, optionally filtered by state."""
        client = self.get_client(params.get("region"))
        filters = []
        if state := params.get("state"):
            filters.append({"Name": "instance-state-name", "Values": [state]})

        response = client.describe_instances(
            Filters=filters,
            MaxResults=params.get("max_results", 100),
        )

        instances: List[Dict[str, Any]] = []
        for reservation in response.get("Reservations", []):
            for inst in reservation.get("Instances", []):
                instances.append(
                    {
                        "instance_id": inst.get("InstanceId"),
                        "type": inst.get("InstanceType"),
                        "state": inst.get("State", {}).get("Name"),
                        "private_ip": inst.get("PrivateIpAddress"),
                        "public_ip": inst.get("PublicIpAddress"),
                        "launch_time": str(inst.get("LaunchTime")),
                        "tags": {t["Key"]: t["Value"] for t in inst.get("Tags", [])},
                    }
                )
        return {"count": len(instances), "instances": instances}

    async def describe_instance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Describe a single instance by ID."""
        client = self.get_client(params.get("region"))
        response = client.describe_instances(
            InstanceIds=[params["instance_id"]],
        )
        reservations = response.get("Reservations", [])
        if not reservations or not reservations[0].get("Instances"):
            return {"found": False, "instance_id": params["instance_id"]}
        return {"found": True, "instance": reservations[0]["Instances"][0]}

    async def start_instance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a stopped EC2 instance."""
        client = self.get_client(params.get("region"))
        response = client.start_instances(InstanceIds=[params["instance_id"]])
        return {"starting": response.get("StartingInstances", [])}

    async def stop_instance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a running EC2 instance."""
        client = self.get_client(params.get("region"))
        response = client.stop_instances(
            InstanceIds=[params["instance_id"]],
            Force=params.get("force", False),
        )
        return {"stopping": response.get("StoppingInstances", [])}

    async def list_security_groups(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List security groups."""
        client = self.get_client(params.get("region"))
        response = client.describe_security_groups(
            MaxResults=params.get("max_results", 100),
        )
        groups = [
            {
                "group_id": g.get("GroupId"),
                "group_name": g.get("GroupName"),
                "description": g.get("Description"),
                "vpc_id": g.get("VpcId"),
            }
            for g in response.get("SecurityGroups", [])
        ]
        return {"count": len(groups), "security_groups": groups}

    async def list_volumes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List EBS volumes."""
        client = self.get_client(params.get("region"))
        response = client.describe_volumes(MaxResults=params.get("max_results", 100))
        volumes = [
            {
                "volume_id": v.get("VolumeId"),
                "size": v.get("Size"),
                "state": v.get("State"),
                "type": v.get("VolumeType"),
                "encrypted": v.get("Encrypted"),
            }
            for v in response.get("Volumes", [])
        ]
        return {"count": len(volumes), "volumes": volumes}
