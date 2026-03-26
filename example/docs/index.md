---
title: "Vex — Cloud API Gateway"
description: "Vex is a self-hosted API gateway for routing, securing, and observing traffic to your backend services."
category: "Getting Started"
order: 1
tags: [overview, introduction]
---

# Vex — Cloud API Gateway

Vex is a lightweight, self-hosted API gateway that sits in front of your backend services. It handles routing, authentication, rate limiting, request transformation, and observability — so your services don't have to.

## Why Vex?

Most API gateways are either too heavy (Kong, AWS API Gateway) or too simple (a plain nginx reverse proxy). Vex hits the sweet spot: it ships as a single binary, is configured with a single YAML file, and exposes a management API for runtime changes without restarts.

## What Vex does

- **Route traffic** — path-based and host-based routing to upstream services
- **Authenticate requests** — API keys, JWT, OAuth2, and mTLS out of the box
- **Rate limit** — per-consumer, per-route, or global limits backed by Redis or in-memory
- **Transform requests and responses** — add/remove headers, rewrite URLs, inject correlation IDs
- **Observe** — Prometheus metrics, structured JSON logs, OpenTelemetry traces

## Architecture overview

```
Client → Vex Gateway → Upstream Services
              ↕
         Plugin chain
         (auth, rate-limit, transform, log)
```

Vex processes each request through a **plugin chain**. Plugins are applied in order and can short-circuit the chain (e.g. an auth plugin that rejects a bad token before the request ever reaches the upstream).

## Next steps

- [Installation](./installation.md) — install the binary or use Docker
- [Quick Start](./quickstart.md) — proxy your first request in under 5 minutes
- [Core Concepts](./concepts.md) — routes, services, consumers, plugins
