---
title: "Deploy to production"
description: "Run llmdocs on a VPS or cloud VM with Docker, TLS, and a reverse proxy. Same pattern for your product docs or this project’s docs/ site."
category: "Deployment"
order: 31
tags: [deploy, production, tls, docker]
---

# Deploy to production

llmdocs is a **long-running HTTP server** (FastAPI + Chroma + embeddings). You deploy it like any other **containerized web app**: one or more instances behind a **reverse proxy** with **TLS**.

It is **not** a static site — there is no GitHub Pages–only path unless you export content elsewhere yourself.

## What you need

- A **host** (VPS, EC2, Fly machine, etc.) with Docker.
- **CPU and RAM** for sentence-transformers (roughly **1–2 GB RAM** minimum for small corpora; more for large indexes).
- **Disk** for Chroma data and Hugging Face cache (persist a volume).
- A **domain** (optional but recommended) for HTTPS.

## 1. Build the search index (recommended before first prod traffic)

On the server or in CI, run once with the same `docs/` tree you will mount:

```bash
llmdocs build --config docs/llmdocs.yaml --data-dir /path/to/persisted/data
```

Or let the first **`llmdocs serve`** run do **lifespan indexing** (slower cold start; model may download on first boot).

## 2. Docker (simplest)

Pull the published image (or build from this repo):

```bash
docker pull vinny2prg/llmdocs-mcp:latest
```

Run with your documentation tree read-only and data persisted:

```bash
docker run -d --name llmdocs --restart unless-stopped \
  -p 127.0.0.1:8080:8080 \
  -v /srv/llmdocs/docs:/docs:ro \
  -v llmdocs_data:/data \
  vinny2prg/llmdocs-mcp:latest
```

- Replace `/srv/llmdocs/docs` with the path to your **`docs/`** directory on the server.
- The image default config uses `docs_dir: /docs` and `llms_txt.output_path: /data/llms.txt` (see `docker/llmdocs.yaml` in the repo).

Bind **`127.0.0.1:8080`** so only the reverse proxy can reach the app; do not expose 8080 to the public internet without TLS in front.

## 3. Docker Compose (from this repo)

From a checkout:

```bash
# Repo root: mount this project’s docs/ as the content
docker compose up -d --build
```

`docker-compose.yml` maps `./docs` → `/docs` and persists `llmdocs_data`. Adjust `image:` to use `vinny2prg/llmdocs-mcp:latest` instead of `build: .` if you prefer not to build locally.

## 4. TLS and HTTPS (Caddy example)

Put **Caddy** or **nginx** on ports 443/80 and proxy to `127.0.0.1:8080`.

**Caddyfile** snippet:

```text
docs.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

Then:

- **HTTP:** `https://docs.example.com/health`
- **MCP:** `https://docs.example.com/mcp/` (trailing slash; many clients need the full URL).

## 5. Environment-specific config

To use a custom `llmdocs.yaml` (different port, weights, model):

```bash
docker run ... \
  -v /srv/llmdocs/llmdocs.yaml:/app/llmdocs.yaml:ro \
  ...
```

Or set **`LLMDOCS_CONFIG`** if your entrypoint respects it (see `Dockerfile` `ENV`).

## 6. Security (v1)

There is **no authentication** on the HTTP/MCP surface by default. For public internet:

- Restrict with **network policy**, **VPN**, or **proxy auth** if docs are private.
- Treat **MCP** as sensitive: do not expose `/mcp/` anonymously if untrusted clients can reach it.

## 7. CI/CD

- **Build image:** tag push (your existing GitHub Action) publishes Docker Hub.
- **Deploy:** SSH + `docker compose pull && docker compose up -d`, or use your platform’s deploy (Kubernetes, ECS, etc.) with the same volume mounts.

## 8. Railway (managed)

For a **GitHub-connected** deploy with minimal ops, see [Deploy on Railway](./railway.md).

## Deploying **this** project’s `docs/` site

On the server, clone or sync the repo and mount **`docs/`** as above. Use **`docs/llmdocs.yaml`** paths by baking a config that sets `docs_dir: /docs` or mount `docs/` at `/docs` and rely on the image default.
