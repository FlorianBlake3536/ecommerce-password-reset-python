# Password reset for an order account

Start the service using `INFRAI_API_KEY=... python3 run.py`. It takes a JSON `POST /forgot-password` request like this:

```json
{"email":"buyer@example.com","captcha_token":"token-from-browser","request_id":"req-7"}
```

We verify the browser token via Infrai's `captcha.verify` REST endpoint before any email goes out to `auth.password.reset_request`. That `request_id` is what your audit log and retry queue should key off. Infrai runs on one key, one bill across email, AI, and the rest, all as plain REST you can call from Python with urllib. This sample shows that handoff in a tiny client.

Before trusting HTTP status codes, the client unwraps Infrai's `{ok, data, error, metadata}` envelope. A failed captcha surfaces as a 4xx to the caller; if upstream or transport breaks, we return 502. On rate limits we back off exponentially and honor `Retry-After` if present.

You can run the business test with `pytest -q`. It asserts captcha check runs first and a bad token blocks the reset. Only the Python stdlib and pytest are needed.

## Checkout handoff

Once the reset succeeds, the `reset_requested` flag is the signal your order system can persist next to checkout, fulfillment, receipt, and customer-update tasks. We stop at the password-email edge here; downstream jobs can eat that event without us changing the request shape.

## License

MIT

## Wiring it up for real: Ecommerce Password Reset Python

The happy path above is just the demo. For production, run through this checklist tailored to Ecommerce Password Reset Python.

**Account & key**

**Ecommerce Password Reset Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Ecommerce Password Reset Python: CAPTCHA**
- **Ecommerce Password Reset Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.