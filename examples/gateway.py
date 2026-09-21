"""Minimal read-only Alexa gateway example.

This file intentionally uses only the Python standard library. It is a teaching
example, not a production deployment.
"""
from __future__ import annotations

import hashlib
import hmac
import html
import json
import os
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

MAX_BODY_BYTES = 64 * 1024
MAX_QUERY_CHARS = 500
MAX_RESPONSE_CHARS = 800
READ_ONLY_INTENTS = {
    "StatusIntent",
    "AskReadOnlyIntent",
    "AMAZON.HelpIntent",
    "AMAZON.StopIntent",
    "AMAZON.CancelIntent",
}


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def verify_signature(body: bytes, timestamp: str, received: str) -> bool:
    """Verify sha256=HMAC(secret, timestamp + newline + body)."""
    secret = env("GATEWAY_SHARED_SECRET").encode("utf-8")
    if not secret or not timestamp or not received:
        return False
    try:
        age = abs(time.time() - int(timestamp))
    except ValueError:
        return False
    if age > int(env("GATEWAY_MAX_SKEW_SECONDS", "300")):
        return False
    material = timestamp.encode("ascii") + b"\n" + body
    expected = hmac.new(secret, material, hashlib.sha256).hexdigest()
    candidate = received.removeprefix("sha256=")
    return hmac.compare_digest(expected, candidate)


def alexa_response(text: str, end_session: bool = False) -> dict:
    safe_text = html.escape(text[:MAX_RESPONSE_CHARS])
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "SSML", "ssml": f"<speak>{safe_text}</speak>"},
            "shouldEndSession": end_session,
        },
    }


def get_slot(slots: dict, *names: str) -> str:
    for name in names:
        value = slots.get(name, {})
        if isinstance(value, dict):
            resolved = value.get("value")
            if isinstance(resolved, str) and resolved.strip():
                return resolved.strip()
    return ""


def call_configured_ai(query: str) -> str:
    """Call an explicitly configured, read-only adapter; never accept a user URL."""
    target = env("AI_API_URL")
    if not target:
        return "O adaptador de IA ainda não foi configurado neste exemplo."
    payload = json_bytes({"input": query, "mode": "read_only"})
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    token = env("AI_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(target, data=payload, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=8) as response:
            result = json.loads(response.read(MAX_BODY_BYTES).decode("utf-8"))
    except Exception:
        return "Não consegui consultar o adaptador de IA agora."
    answer = result.get("answer") if isinstance(result, dict) else None
    if not isinstance(answer, str) or not answer.strip():
        return "O adaptador retornou uma resposta inválida."
    return answer.strip()[:MAX_RESPONSE_CHARS]


def notify_telegram_safely() -> None:
    """Optional notification without forwarding the spoken text or chat history."""
    if env("TELEGRAM_NOTIFY_ON_REQUEST", "false").lower() != "true":
        return
    token = env("TELEGRAM_BOT_TOKEN")
    chat_id = env("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    request = Request(
        endpoint,
        data=json_bytes({"chat_id": chat_id, "text": "Consulta de voz recebida (somente leitura)."}),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=5):
            pass
    except Exception:
        # A notification failure must not make the Alexa request fail.
        pass


def handle_alexa(payload: dict) -> dict:
    request = payload.get("request", {})
    request_type = request.get("type")
    if request_type == "LaunchRequest":
        return alexa_response("Estou pronto para uma consulta de demonstração.")
    if request_type != "IntentRequest":
        return alexa_response("Esse tipo de requisição não é suportado.", True)

    intent = request.get("intent", {})
    name = intent.get("name")
    if name not in READ_ONLY_INTENTS:
        return alexa_response("Esse comando não está habilitado neste starter.", True)
    if name in {"AMAZON.StopIntent", "AMAZON.CancelIntent"}:
        return alexa_response("Até logo.", True)
    if name == "AMAZON.HelpIntent":
        return alexa_response("Você pode pedir o status ou fazer uma pergunta de leitura.")
    if name == "StatusIntent":
        return alexa_response("O gateway de demonstração está online.")

    slots = intent.get("slots", {})
    query = get_slot(slots, "query", "question", "prompt")[:MAX_QUERY_CHARS]
    if not query:
        return alexa_response("Diga qual consulta de leitura você quer fazer.")
    notify_telegram_safely()
    return alexa_response(call_configured_ai(query))


class GatewayHandler(BaseHTTPRequestHandler):
    server_version = "AnnieStarter/0.1"

    def send_json(self, status: int, value: object) -> None:
        data = json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self.send_json(HTTPStatus.OK, {"ok": True, "service": "annie-starter-gateway"})
            return
        self.send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/alexa":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY_BYTES:
            self.send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "invalid_body_size"})
            return
        body = self.rfile.read(length)
        if not verify_signature(
            body,
            self.headers.get("X-Bridge-Timestamp", ""),
            self.headers.get("X-Bridge-Signature", ""),
        ):
            self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "invalid_signature"})
            return
        try:
            payload = json.loads(body.decode("utf-8"))
            response = handle_alexa(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, AttributeError):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            return
        self.send_json(HTTPStatus.OK, response)

    def log_message(self, format: str, *args: object) -> None:
        # Do not log request bodies, prompts or authorization headers.
        print(f"gateway: {format % args}")


def main() -> None:
    host = env("GATEWAY_HOST", "127.0.0.1")
    port = int(env("GATEWAY_PORT", "8765"))
    if not env("GATEWAY_SHARED_SECRET"):
        raise SystemExit("Set GATEWAY_SHARED_SECRET before starting the gateway.")
    server = ThreadingHTTPServer((host, port), GatewayHandler)
    print(f"Listening on http://{host}:{port}; endpoint POST /alexa")
    server.serve_forever()


if __name__ == "__main__":
    main()
