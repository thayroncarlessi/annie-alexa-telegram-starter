"""AWS Lambda adapter between Alexa and the example gateway."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from urllib.request import Request, urlopen


def env(name: str) -> str:
    return os.environ.get(name, "").strip()


def response(text: str) -> dict:
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "SSML", "ssml": f"<speak>{text}</speak>"},
            "shouldEndSession": False,
        },
    }


def application_id(event: dict) -> str:
    session = event.get("session", {})
    context = event.get("context", {})
    return (
        session.get("application", {}).get("applicationId", "")
        or context.get("System", {}).get("application", {}).get("applicationId", "")
    )


def authorized(event: dict) -> bool:
    expected = env("ALEXA_SKILL_ID")
    actual = application_id(event)
    return bool(expected and actual and hmac.compare_digest(expected, actual))


def invoke_gateway(event: dict) -> dict:
    gateway_url = env("GATEWAY_URL").rstrip("/") + "/alexa"
    shared_secret = env("GATEWAY_SHARED_SECRET").encode("utf-8")
    if not gateway_url or not shared_secret:
        raise RuntimeError("Gateway configuration is incomplete")
    body = json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    timestamp = str(int(time.time()))
    material = timestamp.encode("ascii") + b"\n" + body
    signature = hmac.new(shared_secret, material, hashlib.sha256).hexdigest()
    request = Request(
        gateway_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Bridge-Timestamp": timestamp,
            "X-Bridge-Signature": f"sha256={signature}",
        },
        method="POST",
    )
    with urlopen(request, timeout=8) as result:
        return json.loads(result.read(64 * 1024).decode("utf-8"))


def lambda_handler(event: dict, context: object) -> dict:
    """Entry point configured in the Alexa custom skill."""
    del context
    if not isinstance(event, dict) or not authorized(event):
        return response("Não foi possível validar esta skill.")
    try:
        return invoke_gateway(event)
    except Exception:
        # Keep infrastructure details out of the voice response and logs.
        return response("O serviço está temporariamente indisponível.")
