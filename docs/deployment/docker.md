---
title: "Docker"
description: "Run llmdocs in production with the official image: volumes, ports, health checks, and image size notes."
category: "Deployment"
order: 30
tags: [docker, compose, production]
---

# Docker deployment

## Official image

The published image installs locked dependencies and the `llmdocs` CLI as the entrypoint. **CPU-only PyTorch** is used in the image to avoid multi-gigabyte CUDA wheels.

Typical size is on the order of **500–600 MB** — expected for PyTorch + sentence-transformers + Chroma.

## Run

```bash
docker run --rm -p 8080:8080 \
  -v "$(pwd)/docs:/docs:ro" \
  -v llmdocs_data:/data \
  vinny2prg/llmdocs-mcp:latest
```

- Mount your **`docs`** tree read-only at `/docs` (or match `docs_dir` in the baked config).
- Persist **`/data`** for Chroma and generated `llms.txt` if you use the default layout.

## Health check

The image defines a **`HEALTHCHECK`** hitting `/health`. Orchestrators can use the same path.

## docker-compose

Use the repository’s `docker-compose.yml` as a template: adjust image name, ports, and volume paths for your environment.

## Configuration

Override config with **`-e LLMDOCS_CONFIG=...`** or mount a file to `/app/llmdocs.yaml` when the image expects that path (see `Dockerfile` and `docker/llmdocs.yaml` in the repo).

## Embedding providers

By default the container uses **local sentence-transformers** embeddings — the model downloads from Hugging Face on first startup.

To use an **external provider** instead (eliminates the HF download and reduces container startup time), set `embeddings.provider: openai` in your mounted config and pass the API key as an environment variable:

```bash
docker run --rm -p 8080:8080 \
  -v "$(pwd)/docs:/docs:ro" \
  -v llmdocs_data:/data \
  -v "$(pwd)/llmdocs.yaml:/app/llmdocs.yaml:ro" \
  -e OPENAI_API_KEY \
  vinny2prg/llmdocs-mcp:latest
```

With your `llmdocs.yaml`:

```yaml
embeddings:
  provider: openai
  model: text-embedding-3-small
  api_key: ${OPENAI_API_KEY}
```

This works with OpenAI, Azure OpenAI, LiteLLM, or any OpenAI-compatible proxy via `base_url`. See [Configuration — embeddings](../guides/configuration.md#embeddings).

## First-run latency (local embeddings)

When using the default **local** provider, the embedding model downloads on first use (Hugging Face cache). Plan for extra startup time or pre-bake/cache in advanced setups. This does not apply when using `provider: openai`.

## See also

- [Deploy to production](./hosting.md) — TLS, bind addresses, and full hosting checklist.
- [Deploy on Railway](./railway.md) — GitHub + Docker + volume for `/data`.
