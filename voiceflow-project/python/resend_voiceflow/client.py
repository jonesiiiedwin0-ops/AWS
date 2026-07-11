"""
Voiceflow Dialog API client (Python).

Mirrors dialog-api/client.js but in Python using requests. Every request is
also forwarded to the shared Beeceptor webhook for audit/inspection.
"""

import json
import os
import time
from typing import Optional, Dict, Any, List

import requests

WEBHOOK_URL = "https://wh34c025ff0874a90e2f.free.beeceptor.com/"
VOICEFLOW_BASE_URL = os.getenv("VOICEFLOW_BASE_URL", "https://general-runtime.voiceflow.com")


class VoiceflowDialogClient:
    """Low-level client for the Voiceflow Dialog API (v1)."""

    def __init__(
        self,
        api_key: str,
        project_id: str,
        base_url: str = VOICEFLOW_BASE_URL,
        webhook_url: str = WEBHOOK_URL,
        timeout: int = 30,
    ):
        if not api_key:
            raise ValueError("api_key is required")
        if not project_id:
            raise ValueError("project_id is required")
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = base_url.rstrip("/")
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        self._active: Dict[str, Any] = {}

    # -- webhook mirror -------------------------------------------------
    def _forward(self, event_type: str, payload: Dict[str, Any]) -> None:
        try:
            requests.post(
                self.webhook_url,
                json={"type": event_type, "data": payload, "timestamp": time.time()},
                headers={"X-Python-Event": event_type},
                timeout=5,
            )
        except requests.RequestException:
            # Never block the main flow on webhook failure.
            pass

    # -- requests -------------------------------------------------------
    def _request(self, method: str, path: str, body: Optional[Dict] = None) -> Dict:
        url = f"{self.base_url}{path}"
        resp = self.session.request(method, url, json=body, timeout=self.timeout)
        if not resp.ok:
            raise RuntimeError(f"Voiceflow API {resp.status_code}: {resp.text}")
        return resp.json()

    # -- session lifecycle ---------------------------------------------
    def create_session(self, user_id: str, initial_request: Optional[Dict] = None) -> Dict:
        payload = {"projectID": self.project_id, "userID": user_id}
        if initial_request:
            payload["request"] = initial_request
        data = self._request("POST", f"/v1/projects/{self.project_id}/dialogs", payload)
        sid = data.get("dialogID") or data.get("id")
        self._active[sid] = {"state": data.get("state"), "trace": data.get("trace")}
        self._forward("session.created", {"sessionId": sid, "userId": user_id})
        return {"sessionId": sid, **self._parse(data)}

    def send_text(self, session_id: str, text: str) -> Dict:
        return self._send(session_id, {"type": "text", "payload": text})

    def send_intent(self, session_id: str, intent: str, entities: Dict[str, Any]) -> Dict:
        return self._send(session_id, {
            "type": "intent",
            "payload": {"intent": {"name": intent}, "entities": entities},
        })

    def send_choice(self, session_id: str, value: str, label: Optional[str] = None) -> Dict:
        return self._send(session_id, {
            "type": "choice",
            "payload": {"value": value, "label": label or value},
        })

    def _send(self, session_id: str, request: Dict) -> Dict:
        data = self._request(
            "POST",
            f"/v1/projects/{self.project_id}/dialogs/{session_id}/requests",
            {"request": request},
        )
        if session_id in self._active:
            self._active[session_id]["state"] = data.get("state")
            self._active[session_id]["trace"] = data.get("trace")
        self._forward("request.sent", {"sessionId": session_id, "request": request})
        return self._parse(data)

    def end_session(self, session_id: str) -> None:
        try:
            self._request("DELETE", f"/v1/projects/{self.project_id}/dialogs/{session_id}")
        except RuntimeError:
            pass
        self._active.pop(session_id, None)

    # -- parsing --------------------------------------------------------
    @staticmethod
    def _parse(data: Dict) -> Dict:
        messages: List[Dict] = []
        actions: List[Dict] = []
        is_end = False
        for trace in data.get("trace", []) or []:
            t = trace.get("type")
            if t in ("speak", "text"):
                messages.append({"type": t, "content": trace.get("payload", {}).get("message") or trace.get("message")})
            elif t in ("action", "function"):
                actions.append({"type": t, "name": trace.get("payload", {}).get("name"), "params": trace.get("payload")})
            elif t == "end":
                is_end = True
        return {"messages": messages, "actions": actions, "isEnd": is_end, "state": data.get("state")}
