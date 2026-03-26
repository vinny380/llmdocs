---
title: "Rate Limiting"
description: "Protect your upstream services with per-consumer, per-route, and global rate limits."
category: "Core Concepts"
order: 3
tags: [rate-limiting, throttling, redis, protection]
---

# Rate Limiting

The `rate-limit` plugin protects your upstream services from traffic spikes, abuse, and denial-of-service. Vex supports token bucket and sliding window algorithms backed by either in-memory state (single node) or Redis (distributed/cluster).

## Basic configuration

```yaml
plugins:
  - name: rate-limit
    config:
      requests_per_minute: 60
      burst: 10              # allow short bursts above the limit
      backend: memory        # or redis
```

When the limit is exceeded, Vex returns `429 Too Many Requests` with:

```
Retry-After: 14
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1735689600
```

## Limit dimensions

### Global limit

The same counter applies to all consumers and IPs:

```yaml
plugins:
  - name: rate-limit
    config:
      requests_per_minute: 1000
      dimension: global
```

### Per-IP limit

```yaml
plugins:
  - name: rate-limit
    config:
      requests_per_minute: 30
      dimension: ip
      trusted_proxies: [10.0.0.0/8]   # use X-Forwarded-For behind a load balancer
```

### Per-consumer limit

Requires an auth plugin to run first (so the consumer identity is known):

```yaml
plugins:
  - name: api-key
  - name: rate-limit
    config:
      dimension: consumer
      requests_per_minute: 100
```

Consumers on a different plan can have different limits:

```yaml
consumers:
  - name: free-tier-user
    meta:
      rate_limit_rpm: 20
  - name: pro-user
    meta:
      rate_limit_rpm: 1000

plugins:
  - name: rate-limit
    config:
      dimension: consumer
      rpm_from_meta: rate_limit_rpm     # read the limit from consumer metadata
      default_rpm: 20
```

## Redis backend (distributed)

Required when running multiple Vex instances behind a load balancer:

```yaml
plugins:
  - name: rate-limit
    config:
      backend: redis
      redis:
        host: redis.internal
        port: 6379
        password: ${REDIS_PASSWORD}
        db: 0
        key_prefix: vex:rl:
      requests_per_minute: 100
      dimension: consumer
```

Vex uses a Lua script for atomic Redis operations to avoid race conditions.

## Sliding window vs token bucket

| Algorithm | Config value | Behaviour |
|-----------|-------------|-----------|
| Sliding window | `algorithm: sliding_window` | Smooth limiting; no burst allowed |
| Token bucket | `algorithm: token_bucket` (default) | Allows `burst` requests above limit |
| Fixed window | `algorithm: fixed_window` | Resets at the top of each minute |

## Response headers

You can disable rate-limit headers (useful when you don't want to expose limit info to clients):

```yaml
plugins:
  - name: rate-limit
    config:
      hide_headers: true
```

## Exemptions

Bypass rate limiting for specific consumers or IPs:

```yaml
plugins:
  - name: rate-limit
    config:
      requests_per_minute: 60
      exempt_consumers: [internal-service, health-probe]
      exempt_ips: [192.168.1.0/24]
```
