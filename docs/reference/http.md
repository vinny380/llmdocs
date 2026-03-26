---
title: "HTTP API"
description: "HTTP routes: health, OpenAPI, llms.txt, raw markdown, and MCP mount path."
category: "Reference"
order: 21
tags: [http, rest, routes]
---

# HTTP API

The server is **not** a generic REST API for search — use **MCP** for agent-facing search. HTTP is optimized for **health checks**, **machine-readable catalog**, and **raw doc fetch**.

## Routes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | JSON metadata about the service. |
| `GET` | `/health` | `{"status": "healthy", ...}` — use for probes. |
| `GET` | `/docs` | FastAPI **Swagger UI** (OpenAPI). |
| `GET` | `/llms.txt` | Generated or overridden `llms.txt`. |
| `GET` | `/<path>.md` | Markdown **body only** (frontmatter stripped). |

Paths without a `.md` suffix are **not** served as markdown (so `/health` stays safe).

## Security note

There is **no built-in authentication** in v1. Run behind a reverse proxy or private network if your docs are sensitive.
