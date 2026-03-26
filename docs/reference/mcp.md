---
title: "MCP tools"
description: "Streamable HTTP MCP at /mcp/: search_docs, get_doc, list_docs, and client URL requirements."
category: "Reference"
order: 22
tags: [mcp, agents, tools]
---

# MCP tools

llmdocs exposes **FastMCP** over **Streamable HTTP** at:

```text
https://your-host/mcp/
```

**Use a trailing slash.** Many clients mis-route without it (405/406).

## Tools

### `search_docs`

- **Input:** `query` (string), optional `limit` (int).
- **Output:** Ranked chunks with title, description snippet, URL (may include `#anchor`), score.

### `get_doc`

- **Input:** `path` — document path as served (e.g. `/guides/config.md`).
- **Output:** Full markdown body (no frontmatter in content), metadata, URL.

### `list_docs`

- **Input:** optional `category`, optional `path` prefix filter.
- **Output:** List of documents with title, description, path, category.

## Runtime

Tools use the same **Chroma index** and **parser** as the HTTP server. Rebuild the index (`llmdocs build` or `watch`) after large doc changes.

## Clients

For **Cursor**, **VS Code (Copilot)**, and **Claude Code** configuration examples (including `claude mcp add` and `mcp.json`), see [MCP clients: Cursor, VS Code, Claude Code](../guides/mcp-clients.md).
