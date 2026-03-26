---
title: "Quickstart"
description: "Create a project, build the search index, run the server, and connect an MCP client in a few steps."
category: "Getting Started"
order: 3
tags: [tutorial, first-run, mcp]
---

# Quickstart

This walkthrough assumes you installed **`llmdocs-mcp`** and are in an empty or existing project directory.

## 1. Scaffold config and sample doc

```bash
llmdocs init
```

This creates `llmdocs.yaml` and `docs/index.md` (skip if you already have them).

## 2. Add or edit markdown

Put `.md` files under your configured `docs_dir` (default `./docs`). Use YAML frontmatter for title, description, category, and order:

```yaml
---
title: "My page"
description: "One line for search and llms.txt."
category: "Guides"
order: 10
---
```

## 3. Build the index

Search and MCP `search_docs` need a **built index**:

```bash
llmdocs build
```

This writes Chroma data under `.llmdocs/data` (or your `--data-dir`) and generates `llms.txt` if configured.

## 4. Start the server

```bash
llmdocs serve
```

Defaults are in `llmdocs.yaml` (`server.host`, `server.port`).

## 5. Try HTTP endpoints

- `GET /health` — liveness.
- `GET /llms.txt` — generated catalog.
- `GET /your-page.md` — raw markdown (no frontmatter).

## 6. Connect MCP (Streamable HTTP)

Point your MCP client at the **base URL with a trailing slash**:

```text
http://127.0.0.1:8080/mcp/
```

Many clients fail with **405** or **406** if the slash is missing or the request body is wrong — use the official client for your stack.

**Tools:** `search_docs`, `get_doc`, `list_docs`.

## 7. Optional: auto-rebuild on edits

In a second terminal:

```bash
llmdocs watch
```

## Next steps

- [Configuration](../guides/configuration.md) — tune search weights, paths, model.
- [CLI reference](../reference/cli.md) — all commands.
- [MCP reference](../reference/mcp.md) — tool behavior and limits.
