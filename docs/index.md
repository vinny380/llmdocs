---
title: "llmdocs — documentation"
description: "Agent-first, self-hosted documentation: hybrid search, MCP tools, raw markdown URLs, and llms.txt for LLM workflows."
category: "Getting Started"
order: 1
tags: [overview, introduction, open-source]
---

# llmdocs

**llmdocs** is an open-source, **agent-first** documentation stack. Run it beside your markdown docs to give AI tools and humans **semantic + keyword search**, **stable URLs** for raw markdown, **MCP** integration, and an **`llms.txt`** index — without a hosted SaaS or a paid vector API.

## Who it’s for

- **Teams** who want docs searchable by **IDEs and agents** (Cursor, Claude, custom MCP clients).
- **Maintainers** who already write **Markdown + frontmatter** and want **one pipeline** for indexing and HTTP serving.
- **Self-hosters** who prefer **embedded Chroma** and **local embeddings** (default model: `sentence-transformers/all-MiniLM-L6-v2`).

## What you get

| Capability | Description |
|------------|-------------|
| **Hybrid search** | Chroma dense vectors + BM25 keyword fusion over chunked sections. |
| **MCP (Streamable HTTP)** | Tools: `search_docs`, `get_doc`, `list_docs` at `/mcp/`. |
| **Raw markdown** | `GET /<path>.md` returns body without YAML frontmatter. |
| **llms.txt** | Generated catalog of pages; optional manual override. |
| **CLI** | `init`, `serve`, `build`, `validate`, `search`, `watch`. |

## Install in one minute

```bash
pip install llmdocs-mcp
llmdocs init
llmdocs build
llmdocs serve
```

PyPI package name is **`llmdocs-mcp`**; the command-line program is **`llmdocs`**. Requires **Python 3.12+**.

## Where to go next

- [Installation](./getting-started/installation.md) — PyPI, Docker, from source.
- [Quickstart](./getting-started/quickstart.md) — config, index, browser and MCP.
- [Configuration](./guides/configuration.md) — `llmdocs.yaml` reference.
- [Deploy to production](./deployment/hosting.md) — Docker, TLS, reverse proxy.
- [Railway](./deployment/railway.md) — GitHub app, volumes, `PORT`.
- [CLI reference](./reference/cli.md) — all commands and flags.
- [Contributing](./contributing/contributing.md) — issues, PRs, code style.

## License

MIT — see [License](./community/license.md).
