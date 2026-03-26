---
title: "MCP clients: Cursor, VS Code, Claude Code"
description: "Hosted llmdocs MCP for agents plus self-hosted /mcp/: Cursor, VS Code (Copilot), and Claude Code."
category: "Guides"
order: 15
tags: [mcp, cursor, vscode, claude-code, editors]
---

# MCP clients: Cursor, VS Code, Claude Code

## Hosted llmdocs MCP (add to your agents)

There is a **public deployment** that exposes the **llmdocs project documentation** (this repo’s `docs/`) over MCP. Add it to **Cursor**, **Claude Code**, **VS Code**, or any Streamable HTTP MCP client so agents can **`search_docs`**, **`get_doc`**, and **`list_docs`** while helping users with llmdocs — no need to run a server locally for that.

| | |
|--|--|
| **MCP URL** | `https://llmdocs-production.up.railway.app/mcp/` (**trailing slash required**) |
| **Health** | [`https://llmdocs-production.up.railway.app/health`](https://llmdocs-production.up.railway.app/health) |
| **Indexed corpus** | Official llmdocs guides, CLI reference, deployment docs, etc. |

**Cursor** (`~/.cursor/mcp.json` or project `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "llmdocs-docs": {
      "name": "llmdocs",
      "url": "https://llmdocs-production.up.railway.app/mcp/"
    }
  }
}
```

**Claude Code** (CLI — [docs](https://docs.anthropic.com/en/docs/claude-code/mcp)):

```bash
claude mcp add --transport http llmdocs-docs https://llmdocs-production.up.railway.app/mcp/
```

Or **project scope** so everyone in the repo gets the same tools:

```bash
claude mcp add --transport http llmdocs-docs --scope project https://llmdocs-production.up.railway.app/mcp/
```

**VS Code** (workspace `.vscode/mcp.json`):

```json
{
  "servers": {
    "llmdocs-docs": {
      "type": "http",
      "url": "https://llmdocs-production.up.railway.app/mcp/"
    }
  }
}
```

This endpoint has **no login** — it only serves the public documentation index (same content as the open-source `docs/` tree). Treat it like a **read-only public API**: fine for agents answering questions about llmdocs; for **private** docs, [deploy your own](../deployment/hosting.md) and point clients at your URL.

---

## Your own server (self-hosted)

When you run **`llmdocs serve`** or Docker, llmdocs speaks **Streamable HTTP** at **`/mcp/`** (see [MCP tools reference](../reference/mcp.md)). Point clients at your URL **with a trailing slash**.

**Typical URLs**

- **Local:** `http://127.0.0.1:8080/mcp/`
- **Your host:** `https://your-domain.example/mcp/`

Default llmdocs has **no authentication** on HTTP/MCP unless you add a reverse proxy — see [Deploy to production](../deployment/hosting.md).

---

## Claude Code

The **hosted llmdocs** one-liner is at the [top of this page](#hosted-llmdocs-mcp-add-to-your-agents). Below: generic patterns for **your own** server URL.

Anthropic documents remote HTTP MCP in [Connect Claude Code to tools via MCP](https://docs.anthropic.com/en/docs/claude-code/mcp).

### CLI (quick add)

```bash
claude mcp add --transport http llmdocs https://your-host/mcp/
```

Use your real URL; keep the **trailing slash**. For a server only on your machine:

```bash
claude mcp add --transport http llmdocs http://127.0.0.1:8080/mcp/
```

**Scopes** (same doc): add `--scope local` (default, per-project in `~/.claude.json`), `--scope project` (team-shared `.mcp.json` in the repo), or `--scope user` (all projects).

```bash
claude mcp add --transport http llmdocs --scope project https://your-host/mcp/
```

### Project `.mcp.json`

For HTTP servers, Claude Code supports a **`type` + `url`** entry (and optional `headers`). Example you can commit for the team:

```json
{
  "mcpServers": {
    "llmdocs": {
      "type": "http",
      "url": "https://your-host/mcp/"
    }
  }
}
```

If the server requires headers (not the default llmdocs deployment):

```json
{
  "mcpServers": {
    "llmdocs": {
      "type": "http",
      "url": "https://your-host/mcp/",
      "headers": {
        "Authorization": "Bearer ${LLMDOCS_TOKEN}"
      }
    }
  }
}
```

Claude Code may prompt for approval before using project-scoped servers; see `claude mcp reset-project-choices` in the docs.

**Useful commands:** `claude mcp list`, `claude mcp get llmdocs`, `claude mcp remove llmdocs`. Inside Claude Code, `/mcp` lists server status.

---

## Cursor

Cursor reads MCP config from:

- **User:** `~/.cursor/mcp.json` (macOS/Linux) or `%USERPROFILE%\.cursor\mcp.json` (Windows)
- **Project:** `.cursor/mcp.json` in the repo (often checked in so the team shares the same tools)

Project config is merged with user config; restart Cursor after edits so tools reload. Official overview: [Model Context Protocol (MCP) — Cursor](https://cursor.com/docs/context/mcp).

### Example: remote llmdocs (Streamable HTTP)

```json
{
  "mcpServers": {
    "llmdocs": {
      "url": "https://your-host/mcp/"
    }
  }
}
```

Optional display name (if your Cursor version supports it alongside `url`):

```json
{
  "mcpServers": {
    "llmdocs-docs": {
      "name": "llmdocs",
      "url": "https://your-host/mcp/"
    }
  }
}
```

For **local** dev:

```json
{
  "mcpServers": {
    "llmdocs": {
      "url": "http://127.0.0.1:8080/mcp/"
    }
  }
}
```

If your deployment adds auth later, use a `headers` object per Cursor’s MCP docs.

---

## Visual Studio Code (GitHub Copilot)

VS Code discovers MCP servers via **`mcp.json`**: workspace **`.vscode/mcp.json`** (share with the team) or **user** config (**MCP: Open User Configuration**). See [Add and manage MCP servers in VS Code](https://code.visualstudio.com/docs/copilot/customization/mcp-servers) and the [MCP configuration reference](https://code.visualstudio.com/docs/copilot/reference/mcp-configuration).

### Example: HTTP remote server

```json
{
  "servers": {
    "llmdocs": {
      "type": "http",
      "url": "https://your-host/mcp/"
    }
  }
}
```

VS Code uses the top-level key **`servers`** (not `mcpServers`). After saving, reload or let Copilot pick up the server; use **MCP: List Servers** if tools do not appear.

---

## Checklist (all clients)

| Requirement | Notes |
|-------------|--------|
| **Trailing slash** | URL must end with `/mcp/` — many clients get **405/406** without it. |
| **Index built** | Run **`llmdocs build`** (or **`watch`**) so `search_docs` has data. |
| **HTTPS in production** | Use `https://…`; do not append `:8080` on PaaS — the platform maps **443** to your app’s `PORT`. |
| **Trust / security** | Treat unauthenticated `/mcp/` like a public API; restrict by network or proxy if needed. |

---

## Next steps

- [Quickstart](../getting-started/quickstart.md) — run `serve` and smoke-test MCP locally.
- [MCP tools reference](../reference/mcp.md) — `search_docs`, `get_doc`, `list_docs`.
- [Deploy to production](../deployment/hosting.md) — TLS, reverse proxy, locking down MCP.
