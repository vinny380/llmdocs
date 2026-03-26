<p align="center">
  <h1 align="center">llmdocs</h1>
  <p align="center">
    <strong>Documentation your agents can actually search.</strong>
  </p>
  <p align="center">
    Self-hosted stack: <strong>hybrid search</strong> (semantic + keyword), <strong>MCP</strong> tools, raw <code>.md</code> URLs, and <code>llms.txt</code> — no SaaS, no paid vector API required.
  </p>
  <p align="center">
    <strong>📦 <a href="https://pypi.org/project/llmdocs-mcp/">PyPI → llmdocs-mcp</a></strong>
    &nbsp;·&nbsp;
    <strong>🐳 <a href="https://hub.docker.com/r/vinny2prg/llmdocs-mcp">Docker Hub</a></strong>
  </p>
  <p align="center">
    <code>pip install llmdocs-mcp</code> · Python 3.12+ · Embedded Chroma · Local or OpenAI-compatible embeddings
  </p>
  <p align="center">
    <strong>Agents:</strong> add hosted docs MCP →
    <a href="https://llmdocs-production.up.railway.app/mcp/"><code>llmdocs-production.up.railway.app/mcp/</code></a>
    · <a href="#hosted-llmdocs-mcp-for-agents">setup</a>
  </p>
  <p align="center">
    <a href="#get-started">Get Started</a> &middot;
    <a href="#why-llmdocs">Why llmdocs?</a> &middot;
    <a href="#what-you-get">Features</a> &middot;
    <a href="#cli">CLI</a> &middot;
    <a href="#mcp-tools">MCP</a> &middot;
    <a href="#hosted-llmdocs-mcp-for-agents">Agents (hosted MCP)</a> &middot;
    <a href="#http-surface">HTTP</a> &middot;
    <a href="#docker">Docker</a> &middot;
    <a href="#documentation">Docs</a>
  </p>
</p>

---

## Your docs are buried in a repo. Your agent can’t find them.

Paste links into chat and hope for the best? Copy whole folders into context? That doesn’t scale — and RAG pipelines you don’t own are a second job.

**llmdocs** indexes your Markdown (with frontmatter), serves **hybrid search** over real sections, and exposes **MCP** so Cursor, Claude, and custom clients can `search_docs`, `get_doc`, and `list_docs` against *your* corpus. **You** run the server; embeddings stay local by default.

---

## Why llmdocs?

| llmdocs | Typical “docs in chat” |
|---------|-------------------------|
| Indexed **sections** (H2/H3 chunks) + BM25 | Giant paste or ad-hoc grep |
| **Semantic + keyword** fusion | Embeddings only, or keywords only |
| **Stable URLs** — `GET /guide.md` raw body | Screenshots or broken links |
| **MCP** at `/mcp/` (Streamable HTTP) | No standard tool surface |
| **Self-hosted**, local or API embeddings | Another vendor’s vector bill |

---

## Get started

**A few commands.** Install from PyPI (package name **`llmdocs-mcp`**; the program is **`llmdocs`**).

| Step | Action |
|------|--------|
| 1 | `pip install llmdocs-mcp` |
| 2 | `llmdocs init` — detects an existing `docs/` (or `doc/`, `documentation/`) and generates `llmdocs.yaml`. Creates a sample `docs/index.md` only if no docs folder is found. Use `--docs-dir PATH` to point at a specific folder. |
| 3 | `llmdocs build` — index for search + MCP |
| 4 | `llmdocs serve` — HTTP + MCP (use `llmdocs watch` in another terminal for auto-rebuild on save) |

```bash
pip install llmdocs-mcp
llmdocs init
llmdocs build
llmdocs serve
```

From a git checkout (minimal run):

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt && pip install .
llmdocs --help
```

From a git checkout (development):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt && pip install -e .
pytest
```

> **Note:** The CLI is the supported user interface. **`llmdocs` is not a stable Python SDK** — internal modules are implementation details.

---

## What you get

- **Hybrid search** — Chroma semantic vectors + BM25 keyword fusion over chunked sections.
- **MCP (FastMCP, Streamable HTTP)** — `search_docs`, `get_doc`, `list_docs` at **`POST /mcp/`** (use a **trailing slash** in client URLs).
- **Raw markdown** — `GET /<path>.md` returns body without YAML frontmatter.
- **`llms.txt`** — Generated on `llmdocs build` and served at `GET /llms.txt`.
- **CLI** — `init`, `serve`, `build`, `validate`, `search`, `watch`, and more.

Default embedding model: `sentence-transformers/all-MiniLM-L6-v2` (local, no API key needed). Switch to **OpenAI**, **Azure OpenAI**, or any **OpenAI-compatible proxy** (LiteLLM, vLLM) by setting `embeddings.provider: openai` in `llmdocs.yaml` — see [Configuration](https://github.com/vinny380/llmdocs/blob/main/docs/guides/configuration.md#embeddings).

---

## CLI

```bash
llmdocs --version
llmdocs init [--config llmdocs.yaml] [--docs-dir PATH] [--force]
llmdocs build --config llmdocs.yaml
llmdocs serve --config llmdocs.yaml [--host HOST] [--port PORT]
llmdocs validate --config llmdocs.yaml
llmdocs search "your query" --config llmdocs.yaml
llmdocs watch --config llmdocs.yaml   # rebuild on file changes
```

[Full CLI reference →](https://github.com/vinny380/llmdocs/blob/main/docs/reference/cli.md)

---

## MCP tools

| Tool | What it does |
|------|----------------|
| `search_docs` | Hybrid semantic + keyword search over indexed chunks |
| `get_doc` | Full document body + metadata by path |
| `list_docs` | List documents (optional category / path prefix filters) |

[MCP reference →](https://github.com/vinny380/llmdocs/blob/main/docs/reference/mcp.md) · [Quickstart (local URL) →](https://github.com/vinny380/llmdocs/blob/main/docs/getting-started/quickstart.md)

### Hosted llmdocs MCP (for agents)

**Give Cursor, Claude Code, VS Code, and other MCP clients searchable access to this project’s official docs** (install, CLI, Docker, Railway, etc.) — no local `llmdocs serve` required.

| | |
|--|--|
| **MCP URL** | **`https://llmdocs-production.up.railway.app/mcp/`** (keep the **trailing slash**) |
| **Health** | [`/health`](https://llmdocs-production.up.railway.app/health) |

**Cursor** — add to `~/.cursor/mcp.json` or `.cursor/mcp.json`:

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

**Claude Code:** `claude mcp add --transport http llmdocs-docs https://llmdocs-production.up.railway.app/mcp/` (optional: `--scope project` for a shared `.mcp.json`).

**VS Code** (`.vscode/mcp.json`): `"servers": { "llmdocs-docs": { "type": "http", "url": "https://llmdocs-production.up.railway.app/mcp/" } }`.

This is a **public, read-only** docs index (same content as the open `docs/` folder). For **your private** documentation, deploy llmdocs yourself and point clients at **`https://<your-host>/mcp/`**.

Full instructions and self-hosted URLs: **[docs/guides/mcp-clients.md](https://github.com/vinny380/llmdocs/blob/main/docs/guides/mcp-clients.md)**.

### MCP clients (generic)

For **local** dev, point clients at **`http://localhost:8080/mcp/`** (or your `llmdocs.yaml` host/port). llmdocs uses **Streamable HTTP** everywhere.

| Product | Docs |
|---------|------|
| **Claude Code** | [Anthropic: Claude Code + MCP](https://docs.anthropic.com/en/docs/claude-code/mcp) |
| **Cursor** | [Cursor MCP](https://cursor.com/docs/context/mcp) |
| **VS Code** | [VS Code: MCP servers](https://code.visualstudio.com/docs/copilot/customization/mcp-servers) |

---

## HTTP surface

| Route | Description |
|-------|-------------|
| `GET /` | JSON metadata and endpoint index |
| `GET /health` | Liveness JSON (`{"status": "healthy"}`) |
| `POST /mcp/` | Streamable HTTP MCP (**trailing slash**) |
| `GET /<path>.md` | Raw markdown body (no frontmatter) |
| `GET /llms.txt` | Generated catalog (after `llmdocs build`) |

---

## Docker

Image: [`vinny2prg/llmdocs-mcp`](https://hub.docker.com/r/vinny2prg/llmdocs-mcp)

```bash
docker run --rm -p 8080:8080 \
  -v "$(pwd)/docs:/docs:ro" \
  -v llmdocs_data:/data \
  vinny2prg/llmdocs-mcp:latest
```

The repo includes `docker-compose.yml` and a [Railway guide](https://github.com/vinny380/llmdocs/blob/main/docs/deployment/railway.md) — mount a volume on `/data` for persistent Chroma + generated files.

---

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
pytest
```

> **Git:** This repository is **`Projects/llmdocs`**. If your editor opened a parent folder that is also a Git repo, run git commands from the project root so commits apply only to llmdocs.

---

## Project layout (high level)

```
llmdocs/
  cli.py           Click CLI
  config.py        llmdocs.yaml (Pydantic v2)
  server.py        FastAPI + lifespan indexing + /mcp mount
  indexing/        Parser, chunker, Chroma indexer, hybrid search
  mcp/             FastMCP tools + runtime
```

---

## Documentation

| Doc | Description |
|-----|-------------|
| [Installation](https://github.com/vinny380/llmdocs/blob/main/docs/getting-started/installation.md) | PyPI, Docker, from source |
| [Quickstart](https://github.com/vinny380/llmdocs/blob/main/docs/getting-started/quickstart.md) | Config, index, browser & MCP |
| [MCP clients](https://github.com/vinny380/llmdocs/blob/main/docs/guides/mcp-clients.md) | Cursor, VS Code, Claude Code |
| [Configuration](https://github.com/vinny380/llmdocs/blob/main/docs/guides/configuration.md) | `llmdocs.yaml` reference |
| [Hosting](https://github.com/vinny380/llmdocs/blob/main/docs/deployment/hosting.md) | Docker, TLS, reverse proxy |
| [Railway](https://github.com/vinny380/llmdocs/blob/main/docs/deployment/railway.md) | GitHub deploy, volumes, `PORT` |
| [CLI reference](https://github.com/vinny380/llmdocs/blob/main/docs/reference/cli.md) | All commands and flags |
| [Contributing](https://github.com/vinny380/llmdocs/blob/main/docs/contributing/contributing.md) | Issues, PRs, style |

Preview the in-repo docs site locally:

```bash
llmdocs serve --config docs/llmdocs.yaml --data-dir .llmdocs/project-docs
```

Run `llmdocs build --config docs/llmdocs.yaml` first so search works.

---

## License

MIT
