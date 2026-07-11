"""
Day-15 test suite for the Resend AI Agent Python SDK.

Run with:  pytest python/tests -v
Requires: requests, pytest
"""

import os
import sys

import pytest

# Make the package importable when running from the repo root.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "python"))

from resend_voiceflow import ResendAgentClient, WebhookForwarder  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    """Client with network calls stubbed out."""
    c = ResendAgentClient(api_key="vf_test", project_id="proj_test")
    # Stub the underlying HTTP layer.
    monkeypatch.setattr(c, "_request", lambda *a, **k: {
        "dialogID": "sess_123",
        "state": {},
        "trace": [{"type": "speak", "payload": {"message": "✅ Email sent!"}}],
    })
    return c


@pytest.fixture
def forwarder(monkeypatch):
    f = WebhookForwarder()
    # Stub requests.post to avoid touching the network.
    class FakeResp:
        ok = True
        status_code = 200
    monkeypatch.setattr("requests.post", lambda *a, **k: FakeResp())
    return f


def test_create_session(client):
    out = client.create_session("user_1")
    assert out["sessionId"] == "sess_123"
    assert out["messages"][0]["content"] == "✅ Email sent!"


def test_send_email_intent(client):
    out = client.send_email("sess_123", to="a@b.com", subject="Hi", html="<p>hi</p>")
    assert out["messages"]


def test_webhook_forwarder(forwarder):
    res = forwarder.email_sent("email_1", "user@test.com", "Welcome")
    assert res["ok"] is True
    assert res["status"] == 200


def test_webhook_ab_test(forwarder):
    res = forwarder.ab_test_launched("summer", {"variantA": {"sent": 5}, "variantB": {"sent": 5}})
    assert res["ok"] is True


def test_webhook_tenant_event(forwarder):
    res = forwarder.tenant_event("tenant.created", "tenant_abc", "Acme")
    assert res["ok"] is True


def test_webhook_dashboard(forwarder):
    res = forwarder.dashboard_viewed({"period": "7d", "total": 100, "deliveryRate": "98.0"})
    assert res["ok"] is True


def test_high_level_helpers(client):
    for method in [
        lambda: client.check_email_status("sess_123", "email_1"),
        lambda: client.list_emails("sess_123", limit=5),
        lambda: client.verify_domain("sess_123", "example.com"),
        lambda: client.analytics("sess_123", period="30d"),
        lambda: client.manage_tenants("sess_123", action="list"),
        lambda: client.analytics_dashboard("sess_123", period="7d"),
        lambda: client.get_help("sess_123"),
    ]:
        assert method()["messages"]


def test_missing_api_key():
    with pytest.raises(ValueError):
        ResendAgentClient(api_key="", project_id="p")
