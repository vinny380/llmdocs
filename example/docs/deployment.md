---
title: "Deployment"
description: "Run Vex in production: high availability, Kubernetes, systemd, and TLS termination."
category: "Advanced"
order: 1
tags: [deployment, kubernetes, production, ha, systemd, tls]
---

# Deployment

## High availability

For production, run at least two Vex instances behind a load balancer. Since Vex is stateless (all state is in Redis and the config file), you can add or remove instances without downtime.

### Using Redis for shared state

Enable Redis for the rate-limit and response-cache plugins so all instances share the same counters:

```yaml
plugins:
  - name: rate-limit
    config:
      backend: redis
      redis:
        host: redis-cluster.internal
        port: 6380
        sentinel:
          enabled: true
          master_name: vex-redis
          sentinels:
            - host: sentinel-1.internal
              port: 26379
            - host: sentinel-2.internal
              port: 26379
```

### Config synchronisation

Keep all instances in sync by:

1. **Shared config file** — mount the same `vex.yaml` from a network filesystem (NFS, EFS)
2. **Git-ops** — push to a config repo, CI deploys to all instances
3. **Admin API** — use the `/reload` endpoint to push changes to each instance

## Kubernetes

### Helm chart

```bash
helm repo add vex https://charts.vex.dev
helm repo update
helm install vex vex/vex \
  --set proxy.service.type=LoadBalancer \
  --set admin.service.type=ClusterIP \
  --set config.existingSecret=vex-config
```

### Raw manifests

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vex
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vex
  template:
    metadata:
      labels:
        app: vex
    spec:
      containers:
        - name: vex
          image: ghcr.io/example/vex:1.4.2
          ports:
            - containerPort: 8000   # proxy
            - containerPort: 8001   # admin
          livenessProbe:
            httpGet:
              path: /status
              port: 8001
            initialDelaySeconds: 10
          readinessProbe:
            httpGet:
              path: /status
              port: 8001
            initialDelaySeconds: 5
          volumeMounts:
            - name: config
              mountPath: /etc/vex
      volumes:
        - name: config
          secret:
            secretName: vex-config
```

## systemd

```ini
# /etc/systemd/system/vex.service
[Unit]
Description=Vex API Gateway
After=network.target

[Service]
User=vex
ExecStart=/usr/local/bin/vex start --config /etc/vex/vex.yaml
ExecReload=/usr/local/bin/vex reload --config /etc/vex/vex.yaml
Restart=on-failure
RestartSec=5s
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now vex
# Zero-downtime reload:
sudo systemctl reload vex
```

## TLS termination

### At Vex (direct)

```yaml
proxy:
  tls:
    enabled: true
    cert: /etc/vex/tls/fullchain.pem
    key:  /etc/vex/tls/privkey.pem
    min_version: TLS1.2
    ciphers:
      - TLS_AES_128_GCM_SHA256
      - TLS_AES_256_GCM_SHA384
      - TLS_CHACHA20_POLY1305_SHA256
```

Use Let's Encrypt with Certbot and reload Vex after renewal:

```bash
# /etc/letsencrypt/renewal-hooks/deploy/vex.sh
systemctl reload vex
```

### Behind a load balancer

If your load balancer (ALB, nginx, Cloudflare) terminates TLS, configure Vex to trust the `X-Forwarded-For` and `X-Forwarded-Proto` headers:

```yaml
proxy:
  trusted_proxies: [10.0.0.0/8, 172.16.0.0/12]
  forwarded_headers: true
```

## Zero-downtime deploys

Vex implements graceful shutdown: it stops accepting new connections and waits up to `shutdown_timeout` for in-flight requests to complete.

```yaml
proxy:
  shutdown_timeout: 30s
```

Rolling updates in Kubernetes work automatically via the readiness probe. For VM deployments, use a blue-green or rolling strategy at the load balancer level.
