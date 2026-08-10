"""LLM client for agentic operations.

Supports OpenAI, Anthropic, and local providers via pluggable backends.
"""

import logging
import json
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .models import ToolDescriptor

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    """Response from LLM containing reasoning and tool calls."""

    content: str = Field(..., description="AI's response content")
    tool_calls: List[Dict[str, Any]] = Field(
        default_factory=list, description="Sequence of function calls"
    )


class LLMClient:
    """Client for interacting with LLM providers."""

    def __init__(self, api_key: str, model: str, endpoint: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint

    async def get_completion(
        self, prompt: str, tools: List[ToolDescriptor], context: Dict[str, Any]
    ) -> LLMResponse:
        """Generate completion from LLM with available tools.

        Args:
            prompt: User query or system message.
            tools: Available tools for the agent to use.
            context: Session/context for maintaining state.

        Returns:
            Parsed response with content and optional tool calls.
        """
        logger.info("LLM completion called with %d tools", len(tools))
        
        # Mock response for demo - in real implementation this would call an LLM API
        sample_tool_call = {
            "name": "ec2_list_instances",
            "parameters": {"region": "us-east-1"}
        }
        
        return LLMResponse(
            content="I'll help you execute that AWS operation.",
            tool_calls=[sample_tool_call],
        )


class LLMClientManager:
    """Manages multiple LLM clients and routing."""

    def __init__(self):
        self.clients: Dict[str, LLMClient] = {}

    def register_client(self, provider: str, client: LLMClient) -> None:
        """Register an LLM client for a provider."""
        self.clients[provider] = client

    async def get_completion(
        self, provider: str, prompt: str, tools: List[ToolDescriptor], context: Dict[str, Any]
    ) -> LLMResponse:
        """Get completion from registered provider."""
        if provider not in self.clients:
            raise ValueError(f"Provider '{provider}' not registered")
        return await self.clients[provider].get_completion(prompt, tools, context)