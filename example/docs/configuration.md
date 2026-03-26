---
title: "Configuration Reference"
description: "Complete reference for the vex.yaml configuration file with all available options."
category: "Reference"
order: 1
tags: [configuration, yaml, reference, schema]
---

# Configuration Reference

Vex is fully configured via a single `vex.yaml` file. This page documents every available key.

## Top-level structure

```yaml
proxy:          # inbound proxy listener
admin:          # admin API listener
services:       # upstream backends
routes:         # routing rules
consumers:      # authenticated identities
plugins:        # global plugin chain (applied to every request)
logging:        # log format and level
telemetry:      # metrics and tracing
```

## proxy

```yaml
proxy:
  port: 8000              # TCP port (default: 8000)
  host: 0.0.0.0           # bind address (default: 0.0.0.0)
  tls:
    enabled: false
    cert: /etc/vex/tls/server.pem
    key:  /etc/vex/tls/server-key.pem
    min_version: TLS1.2
  read_timeout: 60s       # how long to wait for the full request body
  write_timeout: 60s      # how long to wait before closing the response
  idle_timeout: 120s      # keep-alive connection timeout
  max_request_body: 10MB
```

## admin

```yaml
admin:
  port: 8001
  host: 127.0.0.1         # bind to loopback only (recommended)
  auth:
    enabled: true
    token: ${ADMIN_TOKEN}  # env var expansion is supported
```

> **Warning:** Never expose the Admin API port to the public internet. It allows creating and deleting routes at runtime.

## services

```yaml
services:
  - name: my-api           # unique identifier (required)
    url: http://my-api:3000  # upstream base URL (required)
    connect_timeout: 5s
    read_timeout: 30s
    write_timeout: 30s
    retries: 2             # retry failed requests (connection errors only)
    retry_on: [connection_error, 502, 503, 504]
    tls:
      verify: true         # verify upstream TLS certificate
      ca_cert: /etc/certs/internal-ca.pem
    health_check:
      enabled: true
      path: /health
      interval: 10s
      timeout: 2s
      threshold: 3
```

## routes

```yaml
routes:
  - name: my-route         # unique identifier (required)
    path: /api/v1          # path prefix to match (required)
    host: api.example.com  # optional host header match
    methods: [GET, POST]   # restrict to specific HTTP methods
    service: my-api        # service name (required)
    strip_prefix: true     # remove matched path prefix before forwarding
    preserve_host: false   # forward the original Host header to upstream
    plugins: []            # route-specific plugin chain
```

## consumers

```yaml
consumers:
  - name: my-consumer
    meta:                  # arbitrary key-value metadata (accessible by plugins)
      plan: pro
      team: backend
    credentials:
      - type: api-key
        key: sk_live_abc123
      - type: jwt
        sub: my-consumer@project.iam
```

## logging

```yaml
logging:
  level: info              # debug | info | warn | error
  format: json             # json | text
  output: stdout           # stdout | /var/log/vex.log
  fields:                  # static fields added to every log line
    env: production
    region: us-east-1
```

## telemetry

```yaml
telemetry:
  prometheus:
    enabled: true
    path: /metrics          # exposed on the admin port
  opentelemetry:
    enabled: true
    endpoint: http://otel-collector:4318
    protocol: http/protobuf  # or grpc
    service_name: vex-gateway
    sample_rate: 0.1        # 10% of traces
```

## Environment variable expansion

Any scalar value in the config can reference an environment variable:

```yaml
admin:
  auth:
    token: ${ADMIN_TOKEN}

services:
  - name: db-api
    url: ${DB_API_URL}
```

Vex reads the env at startup. Missing variables cause a fatal error unless a default is provided:

```yaml
token: ${ADMIN_TOKEN:-default-local-token}
```
