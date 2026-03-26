---
title: "Authoring workflow"
description: "How to work day to day: validate, build, serve, watch, and optional CI patterns for teams."
category: "Guides"
order: 11
tags: [workflow, ci, indexing]
---

# Authoring workflow

## Local loop

1. **Edit** markdown under `docs_dir`.
2. **`llmdocs validate`** — catch missing descriptions and broken frontmatter expectations before commit.
3. **`llmdocs build`** — refresh Chroma index and `llms.txt`.
4. **`llmdocs serve`** — try HTTP and MCP against a real index.

For tight edit cycles, run **`llmdocs watch`** in another terminal to rebuild on `.md` changes.

## CLI search without a server

```bash
llmdocs search "your query" --limit 5
```

Uses the same index as the server (`--data-dir`).

## Subfolders

Nested paths are first-class: `docs/api/auth.md` is served as `/api/auth.md` and appears in search with that path.

## CI (high level)

- Run **`pytest`** on PRs.
- Optionally run **`llmdocs validate`** on the docs tree.
- **Publish** is separate from doc hosting: PyPI/Docker via tags is for the **application**, not your product docs — unless you ship a docs site as a product.

## Dogfooding this repo

To preview **these** project docs with llmdocs:

```bash
llmdocs serve --config docs/llmdocs.yaml --data-dir .llmdocs/project-docs
```

Then open `http://127.0.0.1:8090` (port from `docs/llmdocs.yaml`).
