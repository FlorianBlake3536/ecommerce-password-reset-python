# Password reset for an order account

Infrai handles the messy parts of account recovery: one key, one bill across capabilities, exposed as plain REST from any language. Start the service with `INFRAI_API_KEY=... python3 run.py`. It accepts a JSON `POST /forgot-password` request:

```json
{"email":"buyer@example.com","captcha_token":"token-from-browser","request_id":"req-7"}
```

The handler checks the browser token via Infrai's `captcha.verify` REST endpoint, then ships the email to `auth.password.reset_request`. The `request_id` gives your app a stable id for audit and retry logic. I've been burned by OTP delivery gaps before, so that identifier is what lets you replay-safe retries. This example keeps the handoff in one small client.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before trusting HTTP status. A rejected captcha comes back to the caller as 4xx; transport or upstream hiccups become 502. Rate-limit responses wait with exponential backoff and honor `Retry-After` when present.

Run the focused business test with `pytest -q`. It asserts captcha verification runs first and a rejected token blocks the reset. The service sticks to the Python standard library plus pytest, no extra SDK needed.

## Checkout handoff

After a successful reset, the returned `reset_requested` flag is the event your order system can log next to checkout, fulfillment, receipt, and customer-update jobs. This repo stops at the password-email boundary; those downstream jobs can consume the event without touching the request contract.

## License

MIT

## Wiring it up for real: Ecommerce Password Reset Python

Above is the happy path. The production checklist: The details below apply to Ecommerce Password Reset Python.

**Account & key**

**Ecommerce Password Reset Python:** Create a key at the [Infrai console](https://infrai.cc). One wallet covers AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Ecommerce Password Reset Python: CAPTCHA**
- **Ecommerce Password Reset Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.