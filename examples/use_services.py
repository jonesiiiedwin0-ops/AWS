"""Call AWS services directly through the registry (requires real credentials).

This uses only read-only operations so it is safe to run against a real
account. Configure credentials via `aws configure` or environment variables
before running.

Run with:
    python examples/use_services.py
"""

import asyncio

from aws_mcp_server import Config
from aws_mcp_server.services.registry import ServiceRegistry


async def main() -> None:
    config = Config(enabled_services=["s3", "ec2", "iam"])
    registry = ServiceRegistry(config)

    # Verify credentials first so failures are obvious.
    identity = registry.client_manager.verify_credentials()
    if not identity.get("valid"):
        print("Credentials not valid:", identity.get("error"))
        return
    print(f"Authenticated as: {identity['arn']}\n")

    # List S3 buckets.
    buckets = await registry.execute_tool("s3_list_buckets", {})
    print(f"S3 buckets ({buckets['count']}):")
    for bucket in buckets["buckets"]:
        print(f"  - {bucket['name']}")

    # List EC2 instances.
    instances = await registry.execute_tool("ec2_list_instances", {})
    print(f"\nEC2 instances ({instances['count']}):")
    for inst in instances["instances"]:
        print(f"  - {inst['instance_id']} [{inst['state']}] {inst['type']}")

    print("\nCache stats:", registry.cache_stats())


if __name__ == "__main__":
    asyncio.run(main())
