# llmdocs

Agent-first documentation platform — self-hosted, MCP-native, no external vector API required.

Install [`llmdocs-mcp`](https://pypi.org/project/llmdocs-mcp/) from PyPI; the CLI command is `llmdocs`. Requires **Python 3.12+**.

- **MCP tools** via Streamable HTTP (`/mcp/`) for AI agents and IDEs
- **Hybrid search** — Chroma semantic + BM25 keyword fusion
- **Raw markdown URLs** — `GET /guide.md` returns clean content, no frontmatter
- **`llms.txt`** — generated on `llmdocs build` and served at `GET /llms.txt`
- **Embedded Chroma** — no external vector DB needed

---

## Quickstart (CLI)

From [PyPI](https://pypi.org/project/llmdocs-mcp/):

```bash
pip install llmdocs-mcp
llmdocs init
llmdocs build
llmdocs serve
```

Run `llmdocs build` at least once so hybrid search and the MCP `search_docs` tool have an indexed corpus (use `llmdocs watch` in another terminal if you want rebuilds on save).

From a git checkout:

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
| `POST /mcp/` | Streamable HTTP MCP endpoint (FastMCP; **use a trailing slash** for MCP clients) |
| `GET /<path>.md` | Raw markdown body, no frontmatter |

---

## MCP tools

Connect any MCP-compatible client (Cursor, Claude, etc.) to `http://localhost:8080/mcp/` (trailing slash required for Streamable HTTP routing).

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

## Project documentation (this repo)

Long-form docs for users and contributors live under **`docs/`** (Markdown + frontmatter), with config at **`docs/llmdocs.yaml`**. Preview locally:

```bash
llmdocs serve --config docs/llmdocs.yaml --data-dir .llmdocs/project-docs
```

Then open `http://127.0.0.1:8090` (see `docs/llmdocs.yaml` for host/port). Run **`llmdocs build --config docs/llmdocs.yaml`** first so search works.

---

## Docker

Image: [`vinny2prg/llmdocs-mcp`](https://hub.docker.com/r/vinny2prg/llmdocs-mcp) on Docker Hub.

```bash
docker run --rm -p 8080:8080 \
  -v "$(pwd)/docs:/docs:ro" \
  -v llmdocs_data:/data \
  vinny2prg/llmdocs-mcp:latest
```

Or use `docker-compose.yml` in this repo (mount `./docs`, persistent `/data` for Chroma + `llms.txt`). The image ships a default `llmdocs.yaml` under `/app`; override with `-e LLMDOCS_CONFIG=...` or mount your own config.

---

## License

MIT
