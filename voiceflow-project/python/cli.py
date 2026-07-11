#!/usr/bin/env python3
"""
Day-15 CLI for the Resend AI Agent.

Examples
--------
export VOICEFLOW_API_KEY=vf_xxx
export VOICEFLOW_PROJECT_ID=proj_xxx

python python/cli.py chat "Send email to a@b.com subject Hi html <p>hi</p>"
python python/cli.py webhook email.sent '{"email_id":"x","to":"a@b.com","subject":"Hi"}'
python python/cli.py test           # run the pytest suite
"""

import argparse
import json
import os
import subprocess
import sys

# Allow running directly from repo root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python"))

from resend_voiceflow import ResendAgentClient, WebhookForwarder  # noqa: E402


def cmd_chat(args):
    client = ResendAgentClient(
        api_key=os.environ["VOICEFLOW_API_KEY"],
        project_id=os.environ["VOICEFLOW_PROJECT_ID"],
    )
    session = client.create_session("cli_user")
    sid = session["sessionId"]
    result = client.send_text(sid, args.message)
    for m in result["messages"]:
        print(m.get("content", ""))
    client.end_session(sid)


def cmd_webhook(args):
    fwd = WebhookForwarder()
    payload = json.loads(args.json) if args.json else {}
    res = fwd.send(args.event, payload)
    print(json.dumps(res))


def cmd_test(_args):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, "-m", "pytest", os.path.join(root, "python", "tests"), "-v"], check=False)


def main():
    p = argparse.ArgumentParser(description="Resend AI Agent CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("chat", help="Send a text message to the agent")
    c.add_argument("message")
    c.set_defaults(func=cmd_chat)

    w = sub.add_parser("webhook", help="Forward an event to the Beeceptor webhook")
    w.add_argument("event")
    w.add_argument("--json", help="JSON payload")
    w.set_defaults(func=cmd_webhook)

    t = sub.add_parser("test", help="Run the pytest suite")
    t.set_defaults(func=cmd_test)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
