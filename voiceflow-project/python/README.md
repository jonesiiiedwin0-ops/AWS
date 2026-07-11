# Resend AI Agent — Python SDK (Day 15)

A Python backend/CLI/test harness for the Resend AI Agent. It talks to the
Voiceflow **Dialog API** and mirrors every event to the shared Beeceptor
webhook used across all phases:

```
https://wh34c025ff0874a90e2f.free.beeceptor.com/
```

## Install
```bash
pip install -r requirements.txt
```

## Layout
```
python/
├── resend_voiceflow/
│   ├── __init__.py      # exports + WEBHOOK_URL constant
│   ├── client.py        # VoiceflowDialogClient (low-level Dialog API)
│   ├── agent.py         # ResendAgentClient (high-level helpers)
│   └── webhook.py       # WebhookForwarder → Beeceptor
├── tests/
│   └── test_agent.py    # pytest suite (network stubbed)
├── cli.py               # terminal CLI: chat / webhook / test
└── requirements.txt
```

## Quick start
```python
import os
from resend_voiceflow import ResendAgentClient

client = ResendAgentClient(
    api_key=os.environ["VOICEFLOW_API_KEY"],
    project_id=os.environ["VOICEFLOW_PROJECT_ID"],
)
session = client.create_session("user_1")
print(client.send_email(session["sessionId"], to="a@b.com", subject="Hi", html="<p>hi</p>"))
client.end_session(session["sessionId"])
```

## CLI
```bash
export VOICEFLOW_API_KEY=vf_xxx
export VOICEFLOW_PROJECT_ID=proj_xxx

# Talk to the agent
python python/cli.py chat "Send email to a@b.com subject Hi html <p>hi</p>"

# Forward an event to the Beeceptor webhook
python python/cli.py webhook email.sent '{"email_id":"x","to":"a@b.com","subject":"Hi"}'

# Run the test suite
python python/cli.py test
```

## Tests
```bash
pytest python/tests -v
```
Network calls are stubbed, so the suite runs offline and verifies routing,
intent mapping, webhook forwarding, and the high-level helpers.

## Webhook
`WebhookForwarder` exposes `email_sent`, `campaign_scheduled`,
`ab_test_launched`, `tenant_event`, and `dashboard_viewed` helpers — identical
to the JS `handleWebhook.js` / `sendBatch.js` events, all posted to the same
Beeceptor URL.
