"""Configuration management for AWS MCP Server."""

from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Server configuration.

    Values are loaded from (in order of precedence): explicit constructor
    arguments, environment variables, then a ``.env`` file. Field names map to
    upper-cased environment variables (e.g. ``aws_region`` -> ``AWS_REGION``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # AWS Configuration
    aws_region: str = Field(default="us-east-1", description="AWS region")
    aws_access_key_id: Optional[str] = Field(
        default=None, description="AWS access key ID"
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None, description="AWS secret access key"
    )
    aws_profile: Optional[str] = Field(default=None, description="AWS profile name")

    # Server Configuration
    server_host: str = Field(default="0.0.0.0", description="Server host")
    server_port: int = Field(default=8000, description="Server port")
    server_debug: bool = Field(default=False, description="Debug mode")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    # Service Configuration
    enabled_services: List[str] = Field(
        default_factory=lambda: [
            "ec2",
            "s3",
            "lambda",
            "dynamodb",
            "rds",
            "iam",
        ],
        description="List of enabled AWS services",
    )

    # Performance Configuration
    max_connections: int = Field(default=100, description="Max concurrent connections")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")

    # Feature Flags
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")

    @field_validator("enabled_services", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Allow ENABLED_SERVICES to be a comma-separated string from env.

        pydantic-settings would otherwise expect a JSON array for a list
        field; this makes ``ENABLED_SERVICES=ec2,s3,lambda`` work naturally.
        """
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value
