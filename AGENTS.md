# AGENTS.md — guidance for AI and human contributors on llmdocs

This file tells future agents **what this project is**, **how to work on it**, and **boundaries** we have already agreed on. Read `README.md` for install steps; read this for conventions and intent.

---

## Product intent

**llmdocs** is an **agent-first**, **self-hosted** documentation stack: MCP-oriented access, hybrid search (semantic + keyword), raw markdown URLs, and `llms.txt` generation. End users run it **per project** (Docker Compose is the primary consumer path); maintainers use **PyPI** for the CLI.

**Not** a hosted SaaS in v1: embedded Chroma, local embeddings, no required external vector API.

---

## User-facing surface (critical)

- After `pip install llmdocs`, users interact only via the **`llmdocs` CLI** (`[project.scripts]` → `llmdocs.cli:cli`).
- The Python package is **not** a supported public SDK. Do **not** turn `llmdocs/__init__.py` into a barrel of public exports for application code. Internal modules are implementation details.
- **Docker** should run the same code path as the CLI (e.g. container entrypoint eventually calls `llmdocs serve`). Do not fork "Docker-only" behavior unless unavoidable; share logic inside the package.

---

## Distribution (both must stay viable)

1. **PyPI** — CLI and packaging (`pip install llmdocs` or `pip install .` from a checkout).
2. **Docker Hub** — runtime image; `requirements.txt` + `pip install .` pattern for reproducible builds.

When you add or bump dependencies, **refresh locked files** (`requirements.txt` from a clean `pip install .` + `pip freeze`, omit any `llmdocs @ file://...` line) and keep `requirements-dev.txt` in sync for test tooling.

---

## Environment

- Use a **virtualenv** (e.g. `.venv`); it is gitignored.
- **Development:** `pip install -r requirements-dev.txt` then `pip install -e .` (or `pip install -e ".[dev]"` from `pyproject.toml`).
- **Python:** `>=3.12` per `pyproject.toml`.

---

## Testing and TDD

- For **core behavior** (config, parsing, chunking, indexing, search, HTTP/MCP contracts), follow **red → green** TDD: add or adjust a failing test first, then implement.
- Run **`pytest`** before finishing a task; keep coverage meaningful on `llmdocs/` (see `pyproject.toml` pytest/cov options).
- Smoke-test the **CLI** where it matters (e.g. `--version`, subcommands) with `click.testing.CliRunner` or equivalent.
- For **FastAPI** + **lifespan** startup: use `with TestClient(app) as client:` (or equivalent) so **`app.state`** is set before requests hit routes that depend on it.
- **MCP (FastMCP)** tools are exercised with **`fastmcp.client.Client(app.state.mcp)`** in tests (in-process). The public HTTP surface at `/mcp` is **Streamable HTTP MCP**, not REST handlers like `POST /mcp/search_docs`.

---

## Git

- **This repository is rooted in this directory** (`Projects/llmdocs`). Do not assume the parent folder's Git state applies here.
- Use **clear, conventional commits** (e.g. `feat:`, `fix:`, `test:`, `docs:`) and keep changes scoped to the task.

---

## Code style and scope

- **Match existing style**: imports, typing, Pydantic v2 patterns (`model_validator`, `field_validator`, `ConfigDict` — not legacy `class Config`).
- **Minimal diffs:** change only what the task requires; no drive-by refactors or unrelated files.
- **Errors:** align with the product spec where present — graceful handling of bad frontmatter, don't crash the server on Chroma errors (503-style behavior when implemented), etc.

---

## Architecture map (living)

```
llmdocs/
  __init__.py         Version constant; not a public API barrel.
  cli.py              Click commands; user entry point.
  config.py           llmdocs.yaml loading (Pydantic v2).
  models.py           Internal types: Document, Chunk, SearchResult.
  doc_paths.py        Safe URL → filesystem path resolution (used by server + MCP tools).
  server.py           FastAPI app: lifespan indexing, /, /health, /mcp mount, /*.md.

  indexing/           Indexing pipeline subpackage.
    __init__.py       Re-exports all five public classes.
    parser.py         Frontmatter + markdown loading; bad-YAML fallbacks.
    chunker.py        H2/H3 section chunking with tiktoken size limits.
    hasher.py         SHA-256 per file; incremental diff maps.
    indexer.py        Chroma persistent store + sentence-transformers embeddings.
    search.py         HybridSearchEngine: Chroma semantic + BM25 keyword fusion.

  mcp/                MCP subpackage (FastMCP, Streamable HTTP at /mcp).
    __init__.py       Module-level `mcp` + `runtime` singletons; @mcp.tool registrations.
    runtime.py        LlmdocsRuntime dataclass (search_engine, parser, config).
    tools.py          Pure-function tool implementations (search, get, list).
```

**Data flow:**
1. `server.py` lifespan → runs the indexing pipeline (`indexing.*`), builds `HybridSearchEngine`, fills `mcp.runtime` fields.
2. FastMCP mounts at `/mcp`; each tool call injects `runtime` via `Depends(_get_runtime)`.
3. Tool functions in `mcp/tools.py` read from `runtime` and return dicts that FastMCP serialises.

Follow the implementation plan in Bossa Memory / project docs when choosing task order, but **this repo and tests are the source of truth** if anything diverges.

---

## What to avoid

- Treating `llmdocs` as a **stable Python API** for external apps.
- **One-off** dependency installs without updating **locked** requirement files.
- **Huge** AGENTS/README churn — prefer small, accurate updates when behavior changes.

---

## Checklist before you finish a change

1. Tests pass (`pytest`).
2. New or changed behavior for core logic has tests.
3. Dependencies reflected in `pyproject.toml` and locked files where appropriate.
4. CLI/Docker story still coherent (no duplicate entrypoints without reason).
5. Commit from **this** repo if the user asked for version control.
