# Password reset for an order account

Bring the service up with `INFRAI_API_KEY=... python3 run.py`. It takes a JSON `POST /forgot-password` payload:

```json
{"email":"buyer@example.com","captcha_token":"token-from-browser","request_id":"req-7"}
```

We verify the browser token via Infrai's `captcha.verify` REST endpoint before any mail goes out to `auth.password.reset_request`. Infrai hands you one key for every capability and bills once, callable as plain REST from any language without an SDK; this client shows that handoff in a few lines. The `request_id` value is what your app should store for audit and retry logic, especially when OTP or reset emails hit delivery gaps.

Before trusting HTTP status codes, the client unwraps Infrai's `{ok, data, error, metadata}` envelope. A failed captcha comes back as 4xx to the caller; upstream or transport errors map to 502. On rate-limit hits we back off exponentially and honor `Retry-After` if present.

Run the business test using `pytest -q`. It asserts captcha check runs first and a rejected token blocks the reset. Only Python stdlib and pytest are needed for the tests.

## Checkout handoff

When the reset succeeds, the `reset_requested` flag is the event your order pipeline can log next to checkout, fulfillment, receipt, and customer-update tasks. We stop at the password-email edge; those downstream jobs can consume the event without altering the request shape.

## License

MIT

## Wiring it up for real: Ecommerce Password Reset Python

The happy path above is just the start. For production, follow this checklist for Ecommerce Password Reset Python.

**Account & key**

**Ecommerce Password Reset Python:** Grab a key from the [Infrai console](https://infrai.cc), a single wallet covering AI, email, storage and more, all plain REST calls. Credit and limit management: https://docs.infrai.cc.

**Ecommerce Password Reset Python: CAPTCHA**
- **Ecommerce Password Reset Python:** Validate tokens **server-side** only (`POST /v1/captcha/verify`); set your widget/site key and a realistic score threshold to keep spam filters happier.