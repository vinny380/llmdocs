---
title: "Quickstart"
description: "Create a project, build the search index, run the server, and connect an MCP client in a few steps."
category: "Getting Started"
order: 3
tags: [tutorial, first-run, mcp]
---

# Quickstart

This walkthrough assumes you installed **`llmdocs-mcp`** and are in an empty or existing project directory.

## 1. Initialize your project

```bash
llmdocs init
```

If you already have a `docs/`, `doc/`, or `documentation/` folder with markdown files, `init` **detects it automatically** and uses it as `docs_dir` — your existing content is preserved. If no docs folder is found, it creates `docs/index.md` as a starting point.

You can also point at a specific directory:

```bash
llmdocs init --docs-dir my-content
```

Either way, `init` writes an `llmdocs.yaml` config file with sensible defaults.

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

**Editor setup:** To give agents **searchable llmdocs documentation** without running a server, add the **hosted MCP**: `https://llmdocs-production.up.railway.app/mcp/`. Full **Cursor / Claude Code / VS Code** snippets: [MCP clients](../guides/mcp-clients.md#hosted-llmdocs-mcp-add-to-your-agents). For **only your machine**, use `http://127.0.0.1:8080/mcp/` after `llmdocs serve`.

## 7. Optional: auto-rebuild on edits

In a second terminal:

```bash
llmdocs watch
```

## Embedding providers

By default, llmdocs uses a **local** sentence-transformers model — no API key needed, everything runs on your machine.

If you prefer an external provider (OpenAI, Azure OpenAI, or any OpenAI-compatible proxy like LiteLLM), set it in `llmdocs.yaml`:

```yaml
embeddings:
  provider: openai
  model: text-embedding-3-small
  api_key: ${OPENAI_API_KEY}
```

The API key is only needed **server-side** (wherever `llmdocs serve` or `llmdocs build` runs). Clients connecting to your `/mcp/` endpoint never need an API key — the server handles embeddings internally.

See [Configuration — embeddings](../guides/configuration.md#embeddings) for Azure, LiteLLM, and proxy setup.

## Next steps

- [Configuration](../guides/configuration.md) — embeddings, search weights, paths.
- [CLI reference](../reference/cli.md) — all commands and flags.
- [MCP reference](../reference/mcp.md) — tool behavior and limits.
