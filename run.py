import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.password_reset_service import InfraiClient, InfraiError, ResetRequest, request_password_reset


class ResetHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/forgot-password":
            self.send_error(404)
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            request = ResetRequest(body["email"], body["captcha_token"], body["request_id"], self.client_address[0])
            result = request_password_reset(request, InfraiClient())
            self._json(200, result)
        except InfraiError as error:
            self._json(error.status if 400 <= error.status < 500 else 502, {"error": error.code})
        except (KeyError, json.JSONDecodeError):
            self._json(400, {"error": "invalid_request"})
        except Exception:
            self._json(502, {"error": "upstream_unavailable"})

    def _json(self, status: int, value: dict) -> None:
        encoded = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(os.getenv("PORT", "8080"))), ResetHandler).serve_forever()
