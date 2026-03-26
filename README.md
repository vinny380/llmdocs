# llmdocs

Agent-first documentation platform — self-hosted, MCP-native, no external vector API required.

- **MCP tools** via Streamable HTTP (`/mcp`) for AI agents and IDEs
- **Hybrid search** — Chroma semantic + BM25 keyword fusion
- **Raw markdown URLs** — `GET /guide.md` returns clean content, no frontmatter
- **`llms.txt`** generation (coming soon)
- **Embedded Chroma** — no external vector DB needed

---

## Quickstart (CLI)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install .
llmdocs --help
```

The `llmdocs` CLI is the only supported interface. Internal Python modules are implementation details and may change without notice.

---

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
pytest
```

> **Git note:** this repo is rooted in `Projects/llmdocs`. If your editor opened a parent directory that is also a Git repo, run git commands from here so commits apply only to llmdocs.

---

## Server routes

| Route | Description |
|-------|-------------|
| `GET /` | JSON metadata and endpoint index |
| `GET /health` | `{"status": "healthy"}` |
| `POST /mcp` | Streamable HTTP MCP endpoint (FastMCP) |
| `GET /<path>.md` | Raw markdown body, no frontmatter |

---

## MCP tools

Connect any MCP-compatible client (Cursor, Claude, etc.) to `http://localhost:8080/mcp`.

| Tool | Description |
|------|-------------|
| `search_docs` | Hybrid semantic + keyword search over indexed chunks |
| `get_doc` | Fetch full document body and metadata by path |
| `list_docs` | List all documents, optionally filtered by category or path prefix |

---

## Package layout

```
llmdocs/
  cli.py          User entry point (Click commands)
  config.py       llmdocs.yaml loading
  models.py       Internal types (Document, Chunk, SearchResult)
  doc_paths.py    Safe URL → filesystem resolution
  server.py       FastAPI app + lifespan startup indexing

  indexing/       Indexing pipeline
    parser.py     Frontmatter + markdown loading
    chunker.py    H2/H3 section chunking
    hasher.py     SHA-256 file hashing for incremental indexing
    indexer.py    Chroma store + sentence-transformers embeddings
    search.py     HybridSearchEngine (semantic + BM25)

  mcp/            MCP layer (FastMCP, Streamable HTTP at /mcp)
    __init__.py   FastMCP server singleton + tool registrations
    runtime.py    LlmdocsRuntime — state shared between lifespan and tools
    tools.py      Tool logic (pure functions)
```

---

## Docker

The production image installs `requirements.txt` then `pip install .`. A `Dockerfile` and `docker-compose.yml` will be added in a later task.

---

## License

MIT
