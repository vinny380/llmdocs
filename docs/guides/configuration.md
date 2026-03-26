---
title: "Configuration"
description: "Reference for llmdocs.yaml: paths, server, search weights, embeddings, and llms.txt outputs."
category: "Guides"
order: 10
tags: [config, yaml, llmdocs.yaml]
---

# Configuration

`llmdocs` reads **`llmdocs.yaml`** from the path you pass to CLI commands (`--config`).

**Path rules:** Relative paths in the config file (`docs_dir`, `llms_txt.output_path`, `llms_txt.manual_override`) are resolved **relative to the directory containing the config file**, not your shell’s current working directory.

## Minimal example

```yaml
docs_dir: ./docs
server:
  host: 0.0.0.0
  port: 8080
search:
  semantic_weight: 0.7
  keyword_weight: 0.3
  chunk_size: 500
embeddings:
  model: sentence-transformers/all-MiniLM-L6-v2
llms_txt:
  output_path: ./llms.txt
  manual_override: null
```

## `docs_dir`

Root directory for markdown. All `**/*.md` files are loaded **recursively**; URL paths mirror subfolders (e.g. `/guides/setup.md`).

## `server`

| Field | Default | Notes |
|-------|---------|--------|
| `host` | `0.0.0.0` | Bind address. |
| `port` | `8080` | Overridable with `llmdocs serve --port`. |

## `search`

| Field | Default | Notes |
|-------|---------|--------|
| `semantic_weight` | `0.7` | Must sum with `keyword_weight` to **1.0**. |
| `keyword_weight` | `0.3` | BM25 component. |
| `chunk_size` | `500` | Chunking budget (tiktoken-related). |

## `embeddings`

| Field | Default | Notes |
|-------|---------|--------|
| `model` | `sentence-transformers/all-MiniLM-L6-v2` | Sentence-transformers model id; downloaded on first use. |

## `llms_txt`

| Field | Default | Notes |
|-------|---------|--------|
| `output_path` | `./llms.txt` | Written by `llmdocs build`. |
| `manual_override` | `null` | If set to a file path, `GET /llms.txt` serves that file instead of generating. |

## Frontmatter (per document)

Supported fields include:

- `title`, `description` — strongly recommended for search and `llms.txt`.
- `category` — grouping in `llms.txt`.
- `order` — sort within category.
- `tags` — list of strings (YAML scalars).

See `DocumentMetadata` in the codebase for the full schema.
