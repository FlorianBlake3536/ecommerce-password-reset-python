import pytest

from src.password_reset_service import InfraiError, ResetRequest, request_password_reset


class FakeClient:
    def __init__(self):
        self.calls = []

    def post(self, path, body):
        self.calls.append((path, body))
        if path.endswith("captcha/verify"):
            return {"ok": True, "data": {"verified": True}}
        return {"ok": True, "data": {"request_id": "r-1"}}


def test_captcha_gate_precedes_reset_request():
    client = FakeClient()
    result = request_password_reset(ResetRequest("buyer@example.com", "captcha", "req-7"), client)
    assert result["reset_requested"] is True
    assert [path for path, _ in client.calls] == ["/v1/captcha/verify", "/v1/auth/password/reset_request"]


def test_rejected_captcha_stops_reset():
    class Rejecting(FakeClient):
        def post(self, path, body):
            if path.endswith("captcha/verify"):
                raise InfraiError("CAPTCHA_SCORE_TOO_LOW", {}, 422)
            return super().post(path, body)

    with pytest.raises(InfraiError):
        request_password_reset(ResetRequest("buyer@example.com", "bad", "req-8"), Rejecting())
