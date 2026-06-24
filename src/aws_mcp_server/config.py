"""Configuration management for AWS MCP Server."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Config(BaseSettings):
    """Server configuration."""

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    aws_region: str = Field(default="us-east-1", description="AWS region")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    server_host: str = Field(default="0.0.0.0", description="Server host")
    server_port: int = Field(default=8000, description="Server port")
    server_debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format")
    enabled_services: List[str] = Field(
        default_factory=lambda: ["ec2", "s3", "lambda", "dynamodb", "rds", "iam"],
        description="List of enabled AWS services",
    )
    max_connections: int = Field(default=100, description="Max concurrent connections")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
