---
title: "Deploy on Railway"
description: "Connect the GitHub repo, persist /data, use the Dockerfile; PORT is handled automatically."
category: "Deployment"
order: 32
tags: [railway, docker, paas]
---

# Deploy on Railway

Railway works well with this repo’s **Dockerfile**: connect GitHub, build, add a volume for the search index.

## 1. Connect the repo

1. [Railway](https://railway.app) → **New project** → **Deploy from GitHub**.
2. Install the Railway GitHub app on **`vinny380/llmdocs`** (already done if you see the repo).
3. Select the **`llmdocs`** repository.

Railway should detect the **Dockerfile** at the repo root and start a build.

## 2. Persistent volume (Chroma + `llms.txt`)

The container stores the index under **`/data/chroma`** (via `--data-dir /data/chroma`) and writes **`/data/llms.txt`** per `docker/llmdocs.yaml`.

1. Open your **service** → **Volumes** (or **Settings** → **Volumes**, depending on UI).
2. Add a volume and mount it at **`/data`** so **`/data/chroma`** survives restarts.

Without this, every deploy starts with an **empty index** (slow first request, re-embedding).

## 3. Port and health

The image uses **`docker/entrypoint.sh`**, which listens on **`${PORT:-8080}`**. Railway sets **`PORT`** automatically — you usually **do not** need to configure it.

Health checks hit **`/health`**; the Dockerfile `HEALTHCHECK` uses `$PORT` when present.

## 4. Docs content

The Docker build **`COPY`s `docs/`** into **`/docs`**, so **this project’s documentation** ships in the image. To use **your own** markdown instead, mount a volume at **`/docs`** (read-only) in Railway, which overrides the baked-in tree.

## 5. After deploy

- **HTTPS URL** from Railway → **`https://<your-domain>/`**, **`/health`**, **`/llms.txt`**, **`/mcp/`** (keep the **trailing slash** for MCP).
- First cold start may take **minutes** while the **embedding model** downloads to the container filesystem.

## 6. Optional: run `build` on deploy

For faster first search, you can add a **release command** or one-off job that runs **`llmdocs build`** against the same config — not required; **lifespan** indexing on `serve` also populates Chroma.
