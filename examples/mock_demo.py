"""End-to-end demo using moto — no real AWS account required.

Run with:
    pip install "moto>=5"
    python examples/mock_demo.py
"""

import asyncio

from moto import mock_aws

from aws_mcp_server import Config
from aws_mcp_server.services.registry import ServiceRegistry


@mock_aws
def run_demo() -> None:
    import boto3

    config = Config(
        aws_region="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        enabled_services=["s3", "ec2"],
        enable_rate_limiting=False,
    )
    registry = ServiceRegistry(config)

    async def scenario() -> None:
        # Create a bucket through the service layer.
        await registry.execute_tool("s3_create_bucket", {"bucket": "demo-bucket"})

        # Seed an EC2 instance with raw boto3, then list it via the service.
        boto3.client("ec2", region_name="us-east-1").run_instances(
            ImageId="ami-demo123", MinCount=1, MaxCount=1
        )

        buckets = await registry.execute_tool("s3_list_buckets", {})
        instances = await registry.execute_tool("ec2_list_instances", {})

        print("Buckets:", [b["name"] for b in buckets["buckets"]])
        print("Instances:", [i["instance_id"] for i in instances["instances"]])

        # Repeat the read to demonstrate caching.
        await registry.execute_tool("s3_list_buckets", {})
        print("Cache stats:", registry.cache_stats())

    asyncio.run(scenario())


if __name__ == "__main__":
    run_demo()
