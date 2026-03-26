---
title: "Core Concepts"
description: "Understand the building blocks of Vex: services, routes, consumers, and plugins."
category: "Core Concepts"
order: 1
tags: [concepts, architecture, services, routes, plugins]
---

# Core Concepts

Vex is built around four primitives: **services**, **routes**, **consumers**, and **plugins**. Everything else is configuration of these four things.

## Services

A **service** represents an upstream backend — a URL that Vex can forward traffic to.

```yaml
services:
  - name: payments-api
    url: http://payments.internal:3000
    connect_timeout: 5s
    read_timeout: 30s
    retries: 2
```

Services can point to HTTP, HTTPS, or gRPC upstreams. Vex handles TLS termination and re-encryption transparently.

### Health checks

Vex can actively health-check services and remove unhealthy instances from the routing pool:

```yaml
services:
  - name: payments-api
    url: http://payments.internal:3000
    health_check:
      path: /health
      interval: 10s
      threshold: 3        # consecutive failures before marking unhealthy
```

## Routes

A **route** maps an incoming request (matched by path, host, method, or header) to a service.

```yaml
routes:
  - name: payments-v2
    path: /api/v2/payments
    methods: [GET, POST]
    service: payments-api
    strip_prefix: true      # /api/v2/payments/charge → /charge on the upstream
```

### Route matching order

When multiple routes match a request, Vex picks the most specific one — longest prefix wins. If specificity is equal, routes are evaluated in the order they appear in the config.

### Host-based routing

```yaml
routes:
  - name: payments-subdomain
    host: payments.example.com
    path: /
    service: payments-api
```

## Consumers

A **consumer** represents an authenticated identity — a user, service, or machine that makes requests through Vex.

```yaml
consumers:
  - name: mobile-app
    credentials:
      - type: api-key
        key: ak_live_abc123
  - name: partner-xyz
    credentials:
      - type: jwt
        issuer: https://partner-xyz.auth0.com/
```

Consumers are used by auth plugins to attach an identity to a request. Once identified, the consumer name is passed to rate-limit and audit plugins as `X-Consumer-Name`.

## Plugins

**Plugins** are the processing units that run on each request in the proxy pipeline. They are attached to routes, services, or globally.

```yaml
routes:
  - name: payments-v2
    service: payments-api
    plugins:
      - name: jwt            # authenticate
      - name: rate-limit     # then throttle
        config:
          per_consumer: true
          requests_per_minute: 100
      - name: request-id     # then inject correlation ID
```

### Plugin execution order

Plugins run in the order listed. Within that, Vex has two phases per plugin:

1. **Request phase** — runs before the upstream call (auth, rate limit, transform request headers)
2. **Response phase** — runs after the upstream responds (transform response headers, log, cache)

### Scope

| Scope | Applied to |
|-------|-----------|
| Global | Every request through the gateway |
| Service | Every route pointing to that service |
| Route | That specific route only |

More specific scopes override global ones when there's a conflict.
