---
title: "Admin API"
description: "Manage routes, services, consumers, and plugins at runtime via the Vex Admin REST API."
category: "Reference"
order: 3
tags: [admin-api, rest, runtime, management]
---

# Admin API

The Admin API lets you create, read, update, and delete all Vex entities at runtime — without restarting the gateway. It listens on port `8001` (configurable) and should never be exposed to the public internet.

## Base URL

```
http://localhost:8001
```

## Authentication

If `admin.auth.enabled: true` in your config, include the token in every request:

```
Authorization: Bearer <admin-token>
```

## Routes

### List routes

```http
GET /routes
```

```json
{
  "routes": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "payments-v2",
      "path": "/api/v2/payments",
      "service": "payments-api",
      "plugins": ["jwt", "rate-limit"]
    }
  ],
  "total": 1
}
```

### Create a route

```http
POST /routes
Content-Type: application/json

{
  "name": "new-route",
  "path": "/api/v3/orders",
  "service": "orders-api",
  "methods": ["GET", "POST"],
  "plugins": [
    { "name": "api-key" },
    { "name": "rate-limit", "config": { "requests_per_minute": 200 } }
  ]
}
```

Response: `201 Created` with the full route object including its assigned `id`.

### Update a route

```http
PATCH /routes/{name-or-id}
Content-Type: application/json

{
  "plugins": [
    { "name": "api-key" },
    { "name": "rate-limit", "config": { "requests_per_minute": 500 } }
  ]
}
```

Changes take effect immediately for new requests. In-flight requests complete with the old config.

### Delete a route

```http
DELETE /routes/{name-or-id}
```

Response: `204 No Content`. The route stops accepting traffic immediately.

## Services

### List services

```http
GET /services
```

### Create a service

```http
POST /services
Content-Type: application/json

{
  "name": "orders-api",
  "url": "http://orders.internal:4000",
  "read_timeout": "30s",
  "retries": 2
}
```

### Service health status

```http
GET /services/{name}/health
```

```json
{
  "name": "orders-api",
  "status": "healthy",
  "checks": {
    "last_check": "2024-01-15T14:30:00Z",
    "consecutive_successes": 12,
    "consecutive_failures": 0
  }
}
```

## Consumers

### Create a consumer

```http
POST /consumers
Content-Type: application/json

{
  "name": "mobile-app",
  "meta": { "plan": "pro", "team": "mobile" },
  "credentials": [
    { "type": "api-key", "key": "ak_live_mobile_xyz" }
  ]
}
```

### Rotate an API key

```http
POST /consumers/{name}/credentials
Content-Type: application/json

{ "type": "api-key", "key": "ak_live_mobile_new" }
```

Old keys remain valid until explicitly deleted.

### Delete a credential

```http
DELETE /consumers/{name}/credentials/{credential-id}
```

## Global plugins

### List global plugins

```http
GET /plugins
```

### Add a global plugin

```http
POST /plugins
Content-Type: application/json

{
  "name": "request-id",
  "config": { "header_name": "X-Request-Id" }
}
```

## Status and metrics

### Gateway status

```http
GET /status
```

```json
{
  "version": "1.4.2",
  "uptime_seconds": 86400,
  "pid": 12345,
  "goroutines": 42,
  "memory_mb": 38.2
}
```

### Prometheus metrics

```http
GET /metrics
```

Returns the full Prometheus text exposition format. Scrape this endpoint with your Prometheus instance.

## Config reload

Apply changes from the config file without restarting:

```http
POST /reload
```

This is equivalent to `vex reload --config vex.yaml` from the CLI. Entities defined in the config file are reconciled with runtime state; manually-created entities (via the Admin API) are preserved.
