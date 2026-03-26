---
title: "Authentication"
description: "Configure API key, JWT, OAuth2, and mTLS authentication for your routes."
category: "Core Concepts"
order: 2
tags: [authentication, api-key, jwt, oauth2, mtls, security]
---

# Authentication

Vex ships four authentication plugins: `api-key`, `jwt`, `oauth2`, and `mtls`. Each plugin validates the request credentials and, on success, populates the `X-Consumer-Name` header so downstream plugins know who is making the request.

## API Key

The simplest auth method. Credentials are stored in the Vex config or the Admin API.

```yaml
plugins:
  - name: api-key
    config:
      header: X-API-Key        # where to look (default: X-API-Key)
      query_param: api_key     # also accept ?api_key= in query string
      hide_credentials: true   # strip the key before forwarding upstream
```

Create a consumer and attach a key:

```bash
curl -X POST http://localhost:8001/consumers \
  -H "Content-Type: application/json" \
  -d '{"name": "alice", "credentials": [{"type": "api-key", "key": "sk_live_xyz"}]}'
```

Requests must include the key:

```
GET /api/resource HTTP/1.1
X-API-Key: sk_live_xyz
```

Missing or invalid keys receive `401 Unauthorized`.

## JWT

Validates a JSON Web Token in the `Authorization: Bearer <token>` header.

```yaml
plugins:
  - name: jwt
    config:
      algorithm: RS256
      jwks_uri: https://your-idp.example.com/.well-known/jwks.json
      audience: vex-gateway
      leeway: 10s            # clock skew tolerance
      claims_to_headers:
        sub: X-User-Id       # forward JWT claims as upstream headers
        email: X-User-Email
```

Vex fetches the JWKS automatically and rotates keys when the IdP rolls them. The JWKS is cached in memory with a 5-minute TTL.

### Supported algorithms

`HS256`, `HS384`, `HS512`, `RS256`, `RS384`, `RS512`, `ES256`, `ES384`, `ES512`

### Per-consumer JWT validation

You can pin JWTs to specific consumers by matching on the `sub` claim:

```yaml
consumers:
  - name: service-account-ci
    credentials:
      - type: jwt
        sub: ci-pipeline@project.iam
```

## OAuth2

Full OAuth 2.0 token introspection (RFC 7662). Calls your authorization server's introspection endpoint on every request (with caching).

```yaml
plugins:
  - name: oauth2
    config:
      introspection_endpoint: https://auth.example.com/oauth/introspect
      client_id: vex-gateway
      client_secret: ${OAUTH2_CLIENT_SECRET}
      cache_ttl: 60s           # cache valid tokens for 60 seconds
      scopes_required: [read]  # enforce specific scopes
```

Vex supports `client_credentials`, `authorization_code`, and `device_code` flows when acting as an OAuth2 client (for machine-to-machine routes).

## mTLS

Mutual TLS — the client presents a certificate that Vex validates against a trusted CA.

```yaml
plugins:
  - name: mtls
    config:
      ca_cert: /etc/vex/tls/ca.pem
      verify_depth: 2
      allowed_cn:             # optional: allowlist of common names
        - partner.example.com
        - iot-device-fleet
```

The validated certificate's CN is exposed as `X-Client-Cert-CN` to upstream services.

## Combining auth plugins

You can require multiple auth methods on the same route — they all run and all must pass:

```yaml
routes:
  - name: admin
    path: /admin
    plugins:
      - name: mtls          # must present valid cert
      - name: jwt           # AND valid JWT
        config:
          audience: internal-admin
```

Or use the `any-of` combinator to accept either:

```yaml
plugins:
  - name: auth-any-of
    config:
      plugins:
        - name: api-key
        - name: jwt
```
