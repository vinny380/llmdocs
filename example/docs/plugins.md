---
title: "Built-in Plugins"
description: "Reference for all plugins that ship with Vex: auth, rate limiting, transforms, logging, and caching."
category: "Reference"
order: 2
tags: [plugins, reference, transform, cache, cors, logging]
---

# Built-in Plugins

Vex ships with the following plugins. Community plugins are available at [vex-plugins.dev](https://vex-plugins.dev).

## Auth plugins

| Plugin | Purpose |
|--------|---------|
| `api-key` | Validate API keys from header or query string |
| `jwt` | Validate JWT Bearer tokens |
| `oauth2` | Token introspection (RFC 7662) |
| `mtls` | Mutual TLS client certificate validation |
| `basic-auth` | HTTP Basic authentication |
| `auth-any-of` | Accept any one of a list of auth plugins |

See [Authentication](./authentication.md) for full docs.

## Traffic control

### `rate-limit`

See [Rate Limiting](./rate-limiting.md) for full docs.

### `circuit-breaker`

Opens a circuit (stops forwarding to upstream) when the error rate exceeds a threshold.

```yaml
- name: circuit-breaker
  config:
    threshold: 0.5          # open when 50% of requests fail
    window: 10s             # evaluated over a rolling 10-second window
    min_requests: 10        # ignore until at least 10 requests in window
    half_open_requests: 3   # probe with 3 requests before fully closing
```

### `request-size-limit`

```yaml
- name: request-size-limit
  config:
    max_body_bytes: 1048576   # 1 MB
```

## Request / response transforms

### `headers`

Add, remove, or overwrite headers on the request (before upstream) and response (after upstream):

```yaml
- name: headers
  config:
    request:
      add:
        X-Correlation-Id: "{{ uuid }}"
        X-Forwarded-Host: "{{ request.host }}"
      remove: [Authorization]
    response:
      add:
        X-Gateway: vex
        Cache-Control: no-store
      remove: [X-Powered-By, Server]
```

Template variables: `{{ uuid }}`, `{{ request.host }}`, `{{ request.path }}`, `{{ consumer.name }}`, `{{ timestamp }}`.

### `url-rewrite`

```yaml
- name: url-rewrite
  config:
    path_pattern: "^/v1/(.*)"
    path_replacement: "/api/v2/$1"
```

### `body-transform`

Transform JSON request or response bodies using [JMESPath](https://jmespath.org/) expressions:

```yaml
- name: body-transform
  config:
    request:
      - set: "$.metadata.gateway"
        value: "vex"
    response:
      - remove: "$.internal_debug_info"
```

### `request-id`

Injects a unique request ID and propagates it upstream:

```yaml
- name: request-id
  config:
    header_name: X-Request-Id
    generator: uuid4         # uuid4 | nanoid | timestamp
    echo_upstream: true      # forward the ID to the upstream
```

## Caching

### `response-cache`

Cache upstream responses in memory or Redis:

```yaml
- name: response-cache
  config:
    ttl: 60s
    methods: [GET, HEAD]
    vary_by: [X-Consumer-Name, Accept-Language]
    backend: redis
    redis:
      host: redis.internal
      port: 6379
    bypass_header: Cache-Control   # skip cache if this header is "no-cache"
```

Cache keys are built from: method + path + query string + any `vary_by` headers.

## CORS

```yaml
- name: cors
  config:
    origins: ["https://app.example.com", "https://staging.example.com"]
    methods: [GET, POST, PUT, DELETE, OPTIONS]
    headers: [Content-Type, Authorization, X-API-Key]
    expose_headers: [X-Request-Id, X-RateLimit-Remaining]
    credentials: true
    max_age: 3600
```

Use `origins: ["*"]` for development only — never in production with `credentials: true`.

## Observability

### `prometheus`

Exposes per-route metrics on the admin port:

```yaml
- name: prometheus
  config:
    buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
    labels: [route, service, status_code, consumer]
```

### `access-log`

Structured access log per request:

```yaml
- name: access-log
  config:
    format: json
    fields: [method, path, status, latency_ms, consumer, request_id]
    exclude_paths: [/health, /metrics]
```
