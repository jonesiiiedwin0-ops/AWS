"""AWS client manager using boto3 with connection pooling and retry logic."""

import logging
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from .config import Config

logger = logging.getLogger(__name__)


class AWSClientManager:
    """Manages boto3 sessions and clients with caching and retry configuration."""

    def __init__(self, config: Config):
        """Initialize the AWS client manager.

        Args:
            config: Server configuration containing AWS credentials and settings.
        """
        self.config = config
        self._clients: Dict[str, Any] = {}
        self._session: Optional[boto3.Session] = None
        self._boto_config = BotoConfig(
            region_name=config.aws_region,
            retries={
                "max_attempts": config.retry_attempts,
                "mode": "adaptive",
            },
            max_pool_connections=config.max_connections,
            connect_timeout=config.request_timeout,
            read_timeout=config.request_timeout,
        )

    @property
    def session(self) -> boto3.Session:
        """Get or create a boto3 session.

        Returns:
            A configured boto3 Session. Prefers explicit credentials, then a
            named profile, then the default credential chain (env, IAM role).
        """
        if self._session is None:
            session_kwargs: Dict[str, Any] = {"region_name": self.config.aws_region}

            if self.config.aws_access_key_id and self.config.aws_secret_access_key:
                session_kwargs["aws_access_key_id"] = self.config.aws_access_key_id
                session_kwargs["aws_secret_access_key"] = (
                    self.config.aws_secret_access_key
                )
            elif self.config.aws_profile:
                session_kwargs["profile_name"] = self.config.aws_profile

            self._session = boto3.Session(**session_kwargs)
            logger.info("Created boto3 session for region %s", self.config.aws_region)

        return self._session

    def get_client(self, service_name: str, region: Optional[str] = None) -> Any:
        """Get a boto3 client for the given service, caching by service+region.

        Args:
            service_name: AWS service name (e.g. "ec2", "s3").
            region: Optional region override; defaults to configured region.

        Returns:
            A boto3 client for the requested service.
        """
        region = region or self.config.aws_region
        cache_key = f"{service_name}:{region}"

        if cache_key not in self._clients:
            boto_config = self._boto_config.merge(BotoConfig(region_name=region))
            self._clients[cache_key] = self.session.client(
                service_name, config=boto_config
            )
            logger.debug("Created %s client for region %s", service_name, region)

        return self._clients[cache_key]

    def verify_credentials(self) -> Dict[str, Any]:
        """Verify AWS credentials by calling STS GetCallerIdentity.

        Returns:
            A dict with verification status and, on success, caller identity.
        """
        try:
            sts = self.get_client("sts")
            identity = sts.get_caller_identity()
            return {
                "valid": True,
                "account": identity.get("Account"),
                "arn": identity.get("Arn"),
                "user_id": identity.get("UserId"),
            }
        except (ClientError, BotoCoreError) as exc:
            logger.warning("Credential verification failed: %s", exc)
            return {"valid": False, "error": str(exc)}

    def close(self) -> None:
        """Clear cached clients and session."""
        self._clients.clear()
        self._session = None
