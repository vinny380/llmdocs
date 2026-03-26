---
title: "CLI reference"
description: "All llmdocs commands: init, serve, build, validate, search, watch, and global flags."
category: "Reference"
order: 20
tags: [cli, commands, reference]
---

# CLI reference

Invoke **`llmdocs`** after installation (`pip install llmdocs-mcp`). Global options are on the root group (`--help`, `--version`).

## `llmdocs init`

Creates `llmdocs.yaml` and `docs/index.md` if missing.

| Option | Meaning |
|--------|---------|
| `--config PATH` | Where to write config (default `llmdocs.yaml`). |
| `--force` | Overwrite existing files. |

## `llmdocs serve`

Starts the FastAPI server (Uvicorn).

| Option | Meaning |
|--------|---------|
| `--config PATH` | Config file (default `llmdocs.yaml`). |
| `--host`, `--port` | Override server section. |
| `--data-dir PATH` | Chroma and runtime data (default `.llmdocs/data`). |
| `--watch` / `--no-watch` | Uvicorn reload for dev. |

## `llmdocs build`

Incremental index rebuild + `llms.txt` write.

| Option | Meaning |
|--------|---------|
| `--config PATH` | Config file. |
| `--data-dir PATH` | Chroma persistence directory. |

## `llmdocs validate`

Parses all documents and reports issues (e.g. empty description). Exits **1** if problems exist.

## `llmdocs search QUERY`

Hybrid search against the existing index **without** starting the server.

| Option | Meaning |
|--------|---------|
| `--limit N` | Max results (default 5). |
| `--config`, `--data-dir` | Same as above. |

## `llmdocs watch`

Watches `docs_dir` for `*.md` changes and runs the same indexing path as `build` (with debouncing).

## `llmdocs version`

Prints package version.
