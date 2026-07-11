"""
High-level Resend agent client (Python) — convenience methods for every
capability built across Days 1-14.
"""

from typing import Any, Dict, List, Optional

from .client import VoiceflowDialogClient


class ResendAgentClient(VoiceflowDialogClient):
    def send_email(self, session_id: str, *, to: str, subject: str, html: str = None,
                   text: str = None, from_email: str = None, reply_to: str = None,
                   tags: List[str] = None, scheduled_at: str = None) -> Dict:
        return self.send_intent(session_id, "send_email", {
            "to_email": to,
            "email_subject": subject,
            "html_content": html,
            "text_content": text,
            "from_email": from_email,
            "reply_to": reply_to,
            "email_tags": ",".join(tags) if tags else None,
            "scheduled_at": scheduled_at,
        })

    def check_email_status(self, session_id: str, email_id: str) -> Dict:
        return self.send_intent(session_id, "check_email_status", {"email_id": email_id})

    def list_emails(self, session_id: str, *, limit: int = 10, from_date: str = None,
                    to_date: str = None, status: str = None) -> Dict:
        return self.send_intent(session_id, "list_emails", {
            "limit": str(limit),
            "from_date": from_date,
            "to_date": to_date,
            "status": status,
        })

    def verify_domain(self, session_id: str, domain: str) -> Dict:
        return self.send_intent(session_id, "verify_domain", {"domain_name": domain})

    def manage_contact(self, session_id: str, *, action: str, email: str,
                      audience_id: str, first_name: str = None, last_name: str = None,
                      unsubscribed: bool = False) -> Dict:
        return self.send_intent(session_id, "manage_contacts", {
            "action": action,
            "contact_email": email,
            "contact_audience_id": audience_id,
            "contact_first_name": first_name,
            "contact_last_name": last_name,
            "contact_unsubscribed": str(unsubscribed),
        })

    def manage_template(self, session_id: str, *, action: str, **kwargs) -> Dict:
        return self.send_intent(session_id, "manage_templates", {"template_action": action, **kwargs})

    def manage_audience(self, session_id: str, *, action: str, **kwargs) -> Dict:
        return self.send_intent(session_id, "manage_audiences", {"audience_action": action, **kwargs})

    def send_batch(self, session_id: str, *, name: str = None, count: int = 1) -> Dict:
        return self.send_intent(session_id, "send_batch", {
            "batch_name": name, "email_count": str(count)
        })

    def analytics(self, session_id: str, *, period: str = "7d", group_by: str = "day") -> Dict:
        return self.send_intent(session_id, "analytics", {
            "analytics_period": period, "analytics_group_by": group_by
        })

    def run_ab_test(self, session_id: str, *, test_name: str) -> Dict:
        return self.send_intent(session_id, "run_ab_test", {"ab_test_name": test_name})

    def schedule_campaign(self, session_id: str, *, campaign_name: str) -> Dict:
        return self.send_intent(session_id, "schedule_campaign", {"campaign_name": campaign_name})

    def manage_tenants(self, session_id: str, *, action: str, **kwargs) -> Dict:
        return self.send_intent(session_id, "manage_tenants", {"tenant_action": action, **kwargs})

    def manage_workspaces(self, session_id: str, *, action: str, **kwargs) -> Dict:
        return self.send_intent(session_id, "manage_workspaces", {"ws_action": action, **kwargs})

    def analytics_dashboard(self, session_id: str, *, period: str = "7d", workspace: str = None) -> Dict:
        return self.send_intent(session_id, "analytics_dashboard", {
            "dash_period": period, "dash_workspace": workspace
        })

    def manage_whitelabel(self, session_id: str, *, action: str, workspace: str, **kwargs) -> Dict:
        return self.send_intent(session_id, "manage_whitelabel", {
            "wl_action": action, "wl_workspace": workspace, **kwargs
        })

    def get_help(self, session_id: str) -> Dict:
        return self.send_intent(session_id, "help", {})
