---
title: "Development"
description: "Set up a dev environment, run tests, and understand the package layout for contributors."
category: "Contributing"
order: 41
tags: [development, pytest, architecture]
---

# Development

## Environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
```

Python **3.12+** required.

## Tests

```bash
pytest
```

Core behavior (config, parsing, indexing, search, HTTP, MCP, CLI) should stay covered. Use `TestClient` with lifespan for FastAPI tests.

## Layout (high level)

| Area | Role |
|------|------|
| `llmdocs/cli.py` | Click CLI (lazy imports in commands). |
| `llmdocs/config.py` | `llmdocs.yaml` loading; paths relative to config file. |
| `llmdocs/server.py` | FastAPI app, routes, lifespan indexing. |
| `llmdocs/indexing/` | Parser, chunker, hasher, Chroma indexer, hybrid search. |
| `llmdocs/mcp/` | FastMCP tools and runtime. |
| `llmdocs/doc_paths.py` | Safe filesystem resolution for raw `.md` routes. |
| `llmdocs/llms_txt.py` | `llms.txt` generation. |

## Agent notes

Maintainer-oriented conventions live in **`AGENTS.md`** at the repo root.
