---
title: "Troubleshooting"
description: "Diagnose and fix common Vex issues: 502 errors, auth failures, rate limit problems, and high latency."
category: "Troubleshooting"
order: 1
tags: [troubleshooting, errors, debugging, "502", latency]
---

# Troubleshooting

## 502 Bad Gateway

A `502` means Vex reached your upstream service but couldn't get a valid HTTP response.

**Causes and fixes:**

1. **Upstream crashed or restarted** — check `GET /services/{name}/health` on the Admin API; if `status` is `unhealthy`, the service process needs attention.

2. **Wrong upstream URL** — verify the `url` in your service config. A common mistake is `http://` vs `https://` or a missing port number.

3. **TLS mismatch** — if the upstream uses a self-signed cert and `tls.verify: true`, add the CA cert:
   ```yaml
   services:
     - name: my-api
       tls:
         ca_cert: /etc/vex/internal-ca.pem
   ```

4. **Read timeout exceeded** — if your upstream is slow, increase `read_timeout`:
   ```yaml
   services:
     - name: slow-api
       read_timeout: 120s
   ```

Enable debug logging to see the exact error Vex receives from the upstream:

```yaml
logging:
  level: debug
```

## 401 Unauthorized

The request failed authentication.

- **API key plugin:** The key is missing (`X-API-Key` header not present) or the key value doesn't match any consumer credential. Check with `GET /consumers` on the Admin API.
- **JWT plugin:** The token is expired, the signature is invalid, or the audience doesn't match. Run `vex jwt-debug --token <token>` to inspect the claims.
- **OAuth2 plugin:** The introspection endpoint returned `active: false`. Check if the token is expired or was revoked at the IdP.

## 429 Too Many Requests

The consumer or IP hit the rate limit. The `X-RateLimit-Reset` response header tells you when the window resets (Unix timestamp).

If legitimate traffic is being throttled:
- Increase `requests_per_minute` for the affected consumer's metadata
- Or add an exemption: `exempt_consumers: [my-high-volume-service]`

If using Redis as the rate-limit backend, check Redis connectivity:

```bash
curl http://localhost:8001/status | jq .redis
```

## High latency

Use the access log to identify slow routes:

```bash
# Find requests taking more than 500ms
vex logs --follow | jq 'select(.latency_ms > 500)'
```

Common causes:

1. **Slow upstream** — not Vex's fault; check your service directly.
2. **JWKS refresh** — the JWT plugin fetches JWKS on startup and caches it. If you see spikes every 5 minutes, the JWKS TTL expired. Increase `jwks_cache_ttl` or pin the JWKS locally.
3. **Redis latency** — if rate limiting or caching uses Redis, network latency to Redis adds up on every request. Co-locate Redis or switch to `backend: memory` for single-node deployments.
4. **TLS handshake** — if Vex re-establishes TLS connections to the upstream on every request, set `keep_alive: true` on the service.

## Config not reloading

After running `vex reload` or `POST /reload`, changes should apply within milliseconds.

If they don't:
- Check the Vex process logs for a reload error (e.g. YAML parse failure)
- Validate your config: `vex validate --config vex.yaml`
- If running multiple instances, ensure you reloaded all of them

## Memory growing over time

Vex should have stable memory usage. If RSS keeps growing:

1. Check for response-cache entries that never expire (missing `ttl`)
2. Disable `backend: memory` caching in high-throughput environments — use Redis instead to avoid unbounded growth
3. Check `GET /status` for goroutine count — if it keeps rising, file a bug report

## Enabling debug mode

```yaml
logging:
  level: debug
```

Or set the `VEX_LOG_LEVEL=debug` environment variable at runtime without a config change.

Debug logs include: plugin chain execution, upstream connection events, cache hits/misses, and JWT validation steps.
