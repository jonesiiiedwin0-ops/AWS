"""
Webhook forwarder — mirrors Resend/Voiceflow events to the shared Beeceptor
webhook, exactly like the JS-side handleWebhook.js / sendBatch.js.
"""

import time
from typing import Any, Dict, Optional

import requests

WEBHOOK_URL = "https://wh34c025ff0874a90e2f.free.beeceptor.com/"


class WebhookForwarder:
    def __init__(self, webhook_url: str = WEBHOOK_URL, timeout: int = 5):
        self.webhook_url = webhook_url
        self.timeout = timeout

    def send(
        self,
        event_type: str,
        data: Dict[str, Any],
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Forward an event to Beeceptor. Returns a small status dict."""
        headers = {"Content-Type": "application/json", "X-Resend-Event": event_type}
        if extra_headers:
            headers.update(extra_headers)
        payload = {"type": event_type, "data": data, "timestamp": time.time()}
        try:
            resp = requests.post(self.webhook_url, json=payload, headers=headers, timeout=self.timeout)
            return {"ok": resp.ok, "status": resp.status_code}
        except requests.RequestException as exc:
            return {"ok": False, "error": str(exc)}

    # Convenience helpers for common Resend events
    def email_sent(self, email_id: str, to: str, subject: str, variant: str = None, ab_test: str = None) -> Dict:
        data = {"email_id": email_id, "to": to, "subject": subject}
        if variant:
            data["variant"] = variant
        if ab_test:
            data["ab_test"] = ab_test
        return self.send("email.sent", data)

    def campaign_scheduled(self, campaign: str, email_id: str, to: str, scheduled_at: str) -> Dict:
        return self.send("campaign.scheduled", {
            "campaign": campaign, "email_id": email_id, "to": to, "scheduled_at": scheduled_at
        })

    def ab_test_launched(self, test_name: str, summary: Dict) -> Dict:
        return self.send("ab_test.launched", {"test_name": test_name, **summary})

    def tenant_event(self, event: str, tenant_id: str, name: str = None) -> Dict:
        return self.send(event, {"id": tenant_id, "name": name})

    def dashboard_viewed(self, dashboard: Dict) -> Dict:
        return self.send("dashboard.viewed", dashboard)
