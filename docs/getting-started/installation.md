---
title: "Installation"
description: "Install llmdocs from PyPI, Docker, or a git checkout. Python 3.12+, optional Docker for production."
category: "Getting Started"
order: 2
tags: [install, pip, docker, pypi]
---

# Installation

## Requirements

- **Python 3.12 or newer** (see `requires-python` in `pyproject.toml`).
- **Embeddings:** by default, llmdocs uses a local sentence-transformers model (downloaded from Hugging Face on first run, ~100 MB). If you prefer an **external provider** (OpenAI, Azure OpenAI, LiteLLM), set `embeddings.provider: openai` in your config — no local model download needed. See [Configuration — embeddings](../guides/configuration.md#embeddings).
- Enough disk space for **ChromaDB** data — typically tens to hundreds of MB depending on corpus size.

## From PyPI (recommended)

The published package name is **`llmdocs-mcp`**. The CLI is still **`llmdocs`**:

```bash
pip install llmdocs-mcp
llmdocs --version
```

Upgrade later with:

```bash
pip install -U llmdocs-mcp
```

## Docker

Pull the image from Docker Hub (replace with your namespace if you self-build):

```bash
docker pull vinny2prg/llmdocs-mcp:latest
```

Run with your docs mounted read-only and a volume for the index:

```bash
docker run --rm -p 8080:8080 \
  -v "$(pwd)/docs:/docs:ro" \
  -v llmdocs_data:/data \
  vinny2prg/llmdocs-mcp:latest
```

See [Docker deployment](../deployment/docker.md) for `docker-compose` and configuration.

## From source (contributors)

```bash
git clone https://github.com/vinny380/llmdocs.git
cd llmdocs
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
pytest
```

## Verify

```bash
llmdocs validate --config llmdocs.yaml
llmdocs build --config llmdocs.yaml
llmdocs serve --config llmdocs.yaml
```

Then open `http://127.0.0.1:<port>/health` (port from your config).
