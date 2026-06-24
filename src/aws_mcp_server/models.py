"""Pydantic request/response models for the API (drives OpenAPI schema)."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Overall health status", examples=["healthy"])
    services: List[str] = Field(..., description="Initialized AWS services")
    version: str = Field(..., description="Server version")
    credentials_valid: Optional[bool] = Field(
        None, description="Whether AWS credentials verified successfully"
    )


class ServicesResponse(BaseModel):
    """Response listing available and enabled services."""

    available_services: List[str] = Field(..., description="Initialized services")
    enabled_services: List[str] = Field(..., description="Configured services")


class ToolDescriptor(BaseModel):
    """Describes a single executable tool."""

    name: str = Field(..., description="Tool name '<service>_<operation>'")
    service: str = Field(..., description="Owning AWS service")
    operation: str = Field(..., description="Operation name")
    description: str = Field(..., description="Human-readable description")


class ToolsResponse(BaseModel):
    """Response listing all available tools."""

    count: int = Field(..., description="Number of tools")
    tools: List[ToolDescriptor] = Field(..., description="Available tools")


class ExecuteRequest(BaseModel):
    """Request to execute an AWS tool."""

    tool_name: str = Field(
        ...,
        description="Tool to execute, '<service>_<operation>'",
        examples=["ec2_list_instances", "s3_list_buckets"],
    )
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Operation parameters"
    )


class ExecuteResponse(BaseModel):
    """Result of executing a tool."""

    status: str = Field(..., description="'success' or 'error'")
    tool_name: str = Field(..., description="Tool that was executed")
    result: Optional[Any] = Field(None, description="Operation result on success")
    error: Optional[str] = Field(None, description="Error message on failure")


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Machine-readable error code")
