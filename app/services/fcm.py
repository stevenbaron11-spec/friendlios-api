import os, json, time, requests
from typing import List, Dict

# Minimal FCM HTTP v1 sender using OAuth2 with service account credentials.
# For production, you may prefer google-auth library. Here we implement a light JWT flow to avoid heavy deps.

import jwt  # PyJWT
import requests

def _get_sa():
    # Expect path in GOOGLE_APPLICATION_CREDENTIALS or inline JSON in FCM_SERVICE_ACCOUNT_JSON
    path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if path and os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    raw = os.getenv("FCM_SERVICE_ACCOUNT_JSON")
    if raw:
        return json.loads(raw)
    raise RuntimeError("Service account not provided. Set GOOGLE_APPLICATION_CREDENTIALS or FCM_SERVICE_ACCOUNT_JSON.")

def _get_access_token(sa: dict) -> str:
    iat = int(time.time())
    exp = iat + 3600
    payload = {
        "iss": sa["client_email"],
        "scope": "https://www.googleapis.com/auth/firebase.messaging",
        "aud": sa["token_uri"],
        "iat": iat,
        "exp": exp,
    }
    assertion = jwt.encode(payload, sa["private_key"], algorithm="RS256")
    resp = requests.post(sa["token_uri"], data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion
    }, timeout=20)
    resp.raise_for_status()
    return resp.json()["access_token"]

def send_fcm(project_id: str, tokens: List[str], title: str, body: str, data: Dict[str, str] | None = None) -> dict:
    sa = _get_sa()
    access_token = _get_access_token(sa)
    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    results = []
    for tok in tokens:
        msg = {
            "message": {
                "token": tok,
                "notification": {"title": title, "body": body},
                "data": data or {},
            }
        }
        r = requests.post(url, headers=headers, json=msg, timeout=20)
        if r.status_code >= 200 and r.status_code < 300:
            results.append({"token": tok, "ok": True, "resp": r.json()})
        else:
            results.append({"token": tok, "ok": False, "status": r.status_code, "resp": r.text})
    return {"sent": results}
