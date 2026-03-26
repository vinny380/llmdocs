# AGENTS.md — guidance for AI and human contributors on llmdocs

This file tells future agents **what this project is**, **how to work on it**, and **boundaries** we have already agreed on. Read `README.md` for install steps; read this for conventions and intent.

---

## Product intent

**llmdocs** is an **agent-first**, **self-hosted** documentation stack: MCP-oriented access, hybrid search (semantic + keyword), raw markdown URLs, and `llms.txt` generation. End users run it **per project** (Docker Compose is the primary consumer path); maintainers use **PyPI** for the CLI.

**Not** a hosted SaaS in v1: embedded Chroma, local embeddings, no required external vector API.

---

## User-facing surface (critical)

- After `pip install llmdocs`, users interact only via the **`llmdocs` CLI** (`[project.scripts]` → `llmdocs.cli:cli`).
- The Python package is **not** a supported public SDK. Do **not** turn `llmdocs/__init__.py` into a barrel of public exports for application code. Internal modules (`config`, `models`, future `server`, `indexer`, etc.) are implementation details.
- **Docker** should run the same code path as the CLI (e.g. container entrypoint eventually calls `llmdocs serve` or equivalent). Do not fork “Docker-only” behavior unless unavoidable; share logic inside the package.

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

---

## Git

- **This repository is rooted in this directory** (`Projects/llmdocs`). Do not assume the parent folder’s Git state applies here.
- Use **clear, conventional commits** (e.g. `feat:`, `fix:`, `test:`, `docs:`) and keep changes scoped to the task.

---

## Code style and scope

- **Match existing style**: imports, typing, Pydantic v2 patterns (`model_validator`, `field_validator`, `ConfigDict` — not legacy `class Config`).
- **Minimal diffs:** change only what the task requires; no drive-by refactors or unrelated files.
- **Errors:** align with the product spec where present — graceful handling of bad frontmatter, don’t crash the server on Chroma errors (503-style behavior when implemented), etc.

---

## Architecture map (living)

| Area | Notes |
|------|--------|
| `llmdocs/cli.py` | Click commands; user entry. |
| `llmdocs/config.py` | `llmdocs.yaml` loading. |
| `llmdocs/models.py` | Documents, chunks, search results — internal types. |
| `llmdocs/parser.py` | Frontmatter + markdown loading; fallbacks for bad YAML. |
| `llmdocs/chunker.py` | H2/H3 chunking, tiktoken limits. |
| `llmdocs/hasher.py` | SHA-256 per file; incremental diff maps. |
| `llmdocs/indexer.py` | Chroma persistent store + `sentence-transformers` embeddings. |
| `llmdocs/search.py` | `HybridSearchEngine`: Chroma semantic + BM25, `rebuild_index`. |
| `llmdocs/server.py` | FastAPI app, lifespan startup indexing, `/`, `/health`. |
| `llmdocs/mcp.py` | JSON routes: `POST /mcp/search_docs`, `get_doc`, `list_docs`. |
| Future | Raw markdown, `llms.txt`, full CLI, Docker, CI. |

Follow the implementation plan in Bossa Memory / project docs when choosing task order and filenames, but **this repo and tests are the source of truth** if anything diverges.

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
