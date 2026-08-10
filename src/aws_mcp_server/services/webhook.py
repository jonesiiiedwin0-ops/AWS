"""Webhook notification service for external event dispatching.

Receives JSON payloads asynchronously via HTTP POST.
Events are sent as one-way notifications to the configured URL.
"""

import logging
import time
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """Sends notifications to an external webhook endpoint."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self._client = httpx.AsyncClient(timeout=5.0)

    async def send(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send an event notification to the webhook.

        Args:
            event_type: Human-readable event name (e.g. 'tool_executed').
            data: Additional context payload.
        """
        payload = {"event": event_type, "timestamp": time.time(), "data": data}
        try:
            response = await self._client.post(self.webhook_url, json=payload)
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Webhook delivery failed: %s", exc)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()