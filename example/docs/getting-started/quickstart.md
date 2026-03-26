---
title: "Quick Start"
description: "Proxy your first request through Vex in under 5 minutes."
category: "Getting Started"
order: 3
tags: [quickstart, tutorial, first-steps]
---

# Quick Start

This guide walks you through proxying your first request in under 5 minutes. We'll create a route that forwards traffic to `httpbin.org` as a stand-in for a real upstream service.

## Step 1 — Create a config file

Create `vex.yaml`:

```yaml
proxy:
  port: 8000

admin:
  port: 8001

services:
  - name: httpbin
    url: https://httpbin.org

routes:
  - name: anything
    path: /anything
    service: httpbin
    strip_prefix: false
```

## Step 2 — Start Vex

```bash
vex start --config vex.yaml
```

You should see:

```
INFO  vex starting  version=1.4.2
INFO  proxy listening  addr=:8000
INFO  admin listening  addr=:8001
INFO  loaded 1 service, 1 route
```

## Step 3 — Send a request

```bash
curl http://localhost:8000/anything
```

Vex forwards the request to `https://httpbin.org/anything` and returns the response. The `X-Vex-Route` and `X-Vex-Latency-Ms` headers are injected on the way back.

## Step 4 — Inspect the Admin API

```bash
curl http://localhost:8001/routes | jq
```

```json
{
  "routes": [
    {
      "name": "anything",
      "path": "/anything",
      "service": "httpbin",
      "plugins": []
    }
  ]
}
```

## Step 5 — Add an API key plugin

Update `vex.yaml` to protect the route:

```yaml
routes:
  - name: anything
    path: /anything
    service: httpbin
    plugins:
      - name: api-key
        config:
          header: X-API-Key
          keys:
            - name: alice
              key: secret-key-123
```

Reload without downtime:

```bash
vex reload --config vex.yaml
```

Now unauthenticated requests return `401 Unauthorized`. Authenticated requests:

```bash
curl -H "X-API-Key: secret-key-123" http://localhost:8000/anything
```

## What's next?

- [Authentication](./authentication.md) — all auth plugins in depth
- [Rate Limiting](./rate-limiting.md) — protect your upstreams
- [Configuration Reference](./configuration.md) — full YAML schema
