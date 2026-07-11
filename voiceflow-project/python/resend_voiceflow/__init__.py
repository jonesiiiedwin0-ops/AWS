"""
Resend AI Agent — Python SDK
================================

A Python client for the Resend AI Agent built on Voiceflow. Everything that
happens is also mirrored to the shared Beeceptor webhook for inspection and
audit, exactly like the Voiceflow-side functions.

Webhook used throughout: https://wh34c025ff0874a90e2f.free.beeceptor.com/
"""

from .client import VoiceflowDialogClient
from .agent import ResendAgentClient
from .webhook import WebhookForwarder

__all__ = ["VoiceflowDialogClient", "ResendAgentClient", "WebhookForwarder"]

# Shared webhook endpoint (same URL used across all phases).
WEBHOOK_URL = "https://wh34c025ff0874a90e2f.free.beeceptor.com/"
