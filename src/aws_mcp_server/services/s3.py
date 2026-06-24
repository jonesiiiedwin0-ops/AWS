"""S3 service integration."""

from typing import Any, Callable, Dict

from .base import BaseService, ServiceError


class S3Service(BaseService):
    """Simple Storage Service operations."""

    service_name = "s3"
    display_name = "S3"
    description = "Simple Storage Service - scalable object storage"

    def _build_tools(self) -> Dict[str, Callable]:
        return {
            "list_buckets": self.list_buckets,
            "create_bucket": self.create_bucket,
            "delete_bucket": self.delete_bucket,
            "list_objects": self.list_objects,
            "get_object_metadata": self.get_object_metadata,
            "delete_object": self.delete_object,
        }

    async def list_buckets(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all S3 buckets in the account."""
        client = self.get_client(params.get("region"))
        response = client.list_buckets()
        buckets = [
            {
                "name": b.get("Name"),
                "created": str(b.get("CreationDate")),
            }
            for b in response.get("Buckets", [])
        ]
        return {"count": len(buckets), "buckets": buckets}

    async def create_bucket(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new S3 bucket."""
        client = self.get_client(params.get("region"))
        bucket = params["bucket"]
        region = params.get("region", self.client_manager.config.aws_region)

        kwargs: Dict[str, Any] = {"Bucket": bucket}
        # us-east-1 must NOT include a LocationConstraint.
        if region != "us-east-1":
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}

        client.create_bucket(**kwargs)
        return {"created": True, "bucket": bucket, "region": region}

    async def delete_bucket(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an empty S3 bucket."""
        client = self.get_client(params.get("region"))
        client.delete_bucket(Bucket=params["bucket"])
        return {"deleted": True, "bucket": params["bucket"]}

    async def list_objects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List objects in a bucket, optionally under a prefix."""
        client = self.get_client(params.get("region"))
        response = client.list_objects_v2(
            Bucket=params["bucket"],
            Prefix=params.get("prefix", ""),
            MaxKeys=params.get("max_keys", 1000),
        )
        objects = [
            {
                "key": o.get("Key"),
                "size": o.get("Size"),
                "last_modified": str(o.get("LastModified")),
                "storage_class": o.get("StorageClass"),
            }
            for o in response.get("Contents", [])
        ]
        return {
            "bucket": params["bucket"],
            "count": len(objects),
            "truncated": response.get("IsTruncated", False),
            "objects": objects,
        }

    async def get_object_metadata(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get metadata for an object without downloading it."""
        client = self.get_client(params.get("region"))
        if "bucket" not in params or "key" not in params:
            raise ServiceError("'bucket' and 'key' are required", code="InvalidParams")
        response = client.head_object(Bucket=params["bucket"], Key=params["key"])
        return {
            "bucket": params["bucket"],
            "key": params["key"],
            "size": response.get("ContentLength"),
            "content_type": response.get("ContentType"),
            "etag": response.get("ETag"),
            "last_modified": str(response.get("LastModified")),
        }

    async def delete_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an object from a bucket."""
        client = self.get_client(params.get("region"))
        client.delete_object(Bucket=params["bucket"], Key=params["key"])
        return {"deleted": True, "bucket": params["bucket"], "key": params["key"]}
