"""
Command-line interface for llmdocs.

End users invoke `llmdocs` after `pip install llmdocs`. Server and indexing
logic live in other modules and are loaded lazily inside each command so that
`llmdocs --help` stays fast.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from llmdocs import __version__


_DEFAULT_CONFIG = "llmdocs.yaml"
_DEFAULT_DATA_DIR = ".llmdocs/data"

_DEFAULT_CONFIG_YAML = """\
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
"""

_SAMPLE_INDEX_MD = """\
---
title: "Home"
description: "Welcome to the documentation."
category: "General"
order: 1
---

# Home

Welcome to the documentation.
Add your content here.
"""


def _require_config(path: str) -> Path:
    """Return Path to config file, or raise ClickException if it doesn't exist."""
    p = Path(path)
    if not p.exists():
        raise click.ClickException(
            f"Config not found: {p}\nRun `llmdocs init` to create one."
        )
    return p


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="llmdocs")
def cli() -> None:
    """Agent-first documentation platform — CLI only; not a Python SDK."""


@cli.command("version")
def version_cmd() -> None:
    """Print the package version."""
    click.echo(__version__)


@cli.command("init")
@click.option(
    "--config",
    "config_path",
    default=_DEFAULT_CONFIG,
    show_default=True,
    help="Path for the generated config file.",
)
@click.option("--force", is_flag=True, help="Overwrite existing files.")
def init(config_path: str, force: bool) -> None:
    """Scaffold llmdocs.yaml and a sample docs/ directory."""
    cfg_path = Path(config_path)

    if cfg_path.exists() and not force:
        click.echo(f"  skip  {cfg_path} (already exists — use --force to overwrite)")
    else:
        cfg_path.write_text(_DEFAULT_CONFIG_YAML, encoding="utf-8")
        click.echo(f"  create {cfg_path}")

    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    sample = docs_dir / "index.md"
    if sample.exists() and not force:
        click.echo(f"  skip  {sample} (already exists)")
    else:
        sample.write_text(_SAMPLE_INDEX_MD, encoding="utf-8")
        click.echo(f"  create {sample}")

    click.echo("\nNext steps:")
    click.echo("  llmdocs serve    — start the server")
    click.echo("  llmdocs validate — check docs health")


@cli.command("serve")
@click.option(
    "--config",
    "config_path",
    default=_DEFAULT_CONFIG,
    show_default=True,
    help="Path to llmdocs.yaml.",
)
@click.option("--host", default=None, help="Override server host from config.")
@click.option("--port", default=None, type=int, help="Override server port from config.")
@click.option(
    "--data-dir",
    default=_DEFAULT_DATA_DIR,
    show_default=True,
    help="Directory for ChromaDB index storage.",
)
@click.option("--watch/--no-watch", default=False, help="Enable uvicorn hot-reload.")
def serve(
    config_path: str,
    host: Optional[str],
    port: Optional[int],
    data_dir: str,
    watch: bool,
) -> None:
    """Start the documentation server."""
    from llmdocs.config import Config
    from llmdocs.server import run_server

    cfg = Config.load(_require_config(config_path))

    if host or port:
        overrides = {k: v for k, v in {"host": host, "port": port}.items() if v is not None}
        cfg = cfg.model_copy(update={"server": cfg.server.model_copy(update=overrides)})

    data = Path(data_dir)
    data.mkdir(parents=True, exist_ok=True)

    click.echo(f"Starting llmdocs at http://{cfg.server.host}:{cfg.server.port}")
    run_server(cfg, data_dir=data, watch=watch)


@cli.command("build")
@click.option(
    "--config",
    "config_path",
    default=_DEFAULT_CONFIG,
    show_default=True,
    help="Path to llmdocs.yaml.",
)
@click.option(
    "--data-dir",
    default=_DEFAULT_DATA_DIR,
    show_default=True,
    help="Directory for ChromaDB index storage.",
)
def build(config_path: str, data_dir: str) -> None:
    """Pre-build the search index and write llms.txt to disk."""
    from llmdocs.config import Config
    from llmdocs.indexing import DocumentChunker, DocumentIndexer, DocumentParser, FileHasher
    from llmdocs.llms_txt import generate_llms_txt
    from llmdocs.models import Chunk as ChunkModel

    cfg = Config.load(_require_config(config_path))
    data = Path(data_dir)
    data.mkdir(parents=True, exist_ok=True)

    parser = DocumentParser()
    chunker = DocumentChunker(max_chunk_tokens=cfg.search.chunk_size)
    hasher = FileHasher()
    indexer = DocumentIndexer(data_dir=data, embedding_model=cfg.embeddings.model)

    click.echo(f"Indexing {cfg.docs_dir}...")

    current_hashes = hasher.hash_directory(cfg.docs_dir)
    stored_hashes = indexer.get_all_hashes()
    changed, added, deleted = hasher.detect_changes(stored_hashes, current_hashes)

    for doc_path in deleted:
        indexer.delete_by_doc_path(doc_path)

    docs_to_index = list(changed | added)
    if docs_to_index:
        all_docs = parser.load_all(cfg.docs_dir)
        to_reindex = [d for d in all_docs if d.path in docs_to_index]

        for doc in to_reindex:
            doc.file_hash = current_hashes[doc.path]

        all_chunks: list[ChunkModel] = []
        for doc in to_reindex:
            if doc.path in changed:
                indexer.delete_by_doc_path(doc.path)
            chunks = chunker.chunk(doc)
            for ch in chunks:
                ch.metadata["file_hash"] = doc.file_hash
            all_chunks.extend(chunks)

        if all_chunks:
            indexer.index_chunks(all_chunks)

    click.echo(
        f"Done — {len(current_hashes)} doc(s): "
        f"{len(added)} added, {len(changed)} updated, {len(deleted)} removed."
    )

    all_docs = parser.load_all(cfg.docs_dir)
    out_path = cfg.llms_txt.output_path
    out_path.write_text(generate_llms_txt(all_docs), encoding="utf-8")
    click.echo(f"Written {out_path}")


@cli.command("validate")
@click.option(
    "--config",
    "config_path",
    default=_DEFAULT_CONFIG,
    show_default=True,
    help="Path to llmdocs.yaml.",
)
def validate(config_path: str) -> None:
    """Parse all docs and report any health issues."""
    from llmdocs.config import Config
    from llmdocs.indexing import DocumentParser

    cfg = Config.load(_require_config(config_path))
    parser = DocumentParser()
    docs = parser.load_all(cfg.docs_dir)

    issues: list[tuple[str, str]] = []
    for doc in docs:
        if not doc.description:
            issues.append((doc.path, "missing description"))

    if issues:
        for path, msg in issues:
            click.echo(f"  WARN  {path}: {msg}")
        click.echo(f"\n{len(issues)} issue(s) found in {len(docs)} doc(s).")
        sys.exit(1)

    click.echo(f"OK — {len(docs)} doc(s), no issues found.")
