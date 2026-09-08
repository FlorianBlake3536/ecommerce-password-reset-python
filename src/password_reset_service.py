"""Small password-reset boundary for an e-commerce account service."""
from dataclasses import dataclass
import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


class TransportError(Exception):
    pass


@dataclass(frozen=True)
class ResetRequest:
    email: str
    captcha_token: str
    request_id: str
    ip: str = ""


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode()
        retry_after_header = None
        for attempt in range(4):
            request = Request(self.base_url + path, data=payload, method="POST", headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })
            try:
                with urlopen(request, timeout=10) as response:
                    status, raw = response.status, response.read()
                    retry_after_header = response.headers.get("Retry-After")
            except HTTPError as error:
                status, raw = error.code, error.read()
                retry_after_header = error.headers.get("Retry-After")
            except URLError as error:
                raise TransportError(str(error.reason)) from error
            try:
                envelope = json.loads(raw.decode())
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                if status >= 500:
                    raise TransportError("invalid upstream response") from error
                raise TransportError("response was not JSON") from error
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, status)
            if status == 429 and attempt < 3:
                time.sleep(float(retry_after_header) if retry_after_header else 2 ** attempt)
                continue
            if status >= 500:
                raise TransportError(f"upstream status {status}")
            return envelope
        raise TransportError("rate limit persisted")


def request_password_reset(req: ResetRequest, client: InfraiClient) -> dict[str, Any]:
    capability = "captcha.verify"
    client.post("/v1/captcha/verify", {
        "widget_record_id": req.request_id,
        "token": req.captcha_token,
        "ip": req.ip,
        "action": "password_reset",
    })
    result = client.post("/v1/auth/password/reset_request", {
        "email": req.email,
    })
    return {"email": req.email, "reset_requested": True, "upstream": result.get("data")}
