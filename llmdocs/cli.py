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

_CANDIDATE_DOC_DIRS = ("docs", "doc", "documentation")


def _make_config_yaml(docs_dir: str = "./docs") -> str:
    return f"""\
docs_dir: {docs_dir}
server:
  host: 0.0.0.0
  port: 8080
search:
  semantic_weight: 0.7
  keyword_weight: 0.3
  chunk_size: 500
embeddings:
  provider: local
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


def _detect_docs_dir() -> tuple[Path, int] | None:
    """Find an existing directory with markdown files.

    Returns ``(path, md_count)`` for the first candidate that contains at
    least one ``.md`` file, or ``None`` if nothing is found.
    """
    for name in _CANDIDATE_DOC_DIRS:
        candidate = Path(name)
        if candidate.is_dir():
            md_count = sum(1 for _ in candidate.rglob("*.md"))
            if md_count > 0:
                return candidate, md_count
    return None


@cli.command("init")
@click.option(
    "--config",
    "config_path",
    default=_DEFAULT_CONFIG,
    show_default=True,
    help="Path for the generated config file.",
)
@click.option(
    "--docs-dir",
    "docs_dir_opt",
    default=None,
    help="Path to an existing docs directory (overrides auto-detection).",
)
@click.option("--force", is_flag=True, help="Overwrite existing files.")
def init(config_path: str, docs_dir_opt: str | None, force: bool) -> None:
    """Scaffold llmdocs.yaml, detecting an existing docs directory if present."""
    cfg_path = Path(config_path)

    # --- resolve docs directory -------------------------------------------
    detected = _detect_docs_dir()
    if docs_dir_opt is not None:
        docs_dir = Path(docs_dir_opt)
        existing = docs_dir.is_dir() and any(docs_dir.rglob("*.md"))
    elif detected is not None:
        docs_dir, md_count = detected
        existing = True
        click.echo(
            f"  found  {docs_dir}/ ({md_count} markdown file{'s' if md_count != 1 else ''}) "
            f"— using as docs_dir"
        )
    else:
        docs_dir = Path("docs")
        existing = False

    # --- write config file ------------------------------------------------
    docs_dir_value = f"./{docs_dir}" if not str(docs_dir).startswith("./") else str(docs_dir)
    if cfg_path.exists() and not force:
        click.echo(f"  skip  {cfg_path} (already exists — use --force to overwrite)")
    else:
        cfg_path.write_text(_make_config_yaml(docs_dir_value), encoding="utf-8")
        click.echo(f"  create {cfg_path}")

    # --- scaffold docs directory only when creating fresh -----------------
    if existing:
        click.echo(f"  using  {docs_dir}/ (existing docs preserved)")
    else:
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
@click.option(
    "--port", default=None, type=int, help="Override server port from config."
)
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
        overrides = {
            k: v for k, v in {"host": host, "port": port}.items() if v is not None
        }
        cfg = cfg.model_copy(update={"server": cfg.server.model_copy(update=overrides)})

    data = Path(data_dir)
    data.mkdir(parents=True, exist_ok=True)

    click.echo(f"Starting llmdocs at http://{cfg.server.host}:{cfg.server.port}")
    run_server(cfg, data_dir=data, watch=watch)


def _index_docs(cfg: "Config", data: Path) -> tuple[int, int, int]:
    """Shared core: incremental index rebuild + llms.txt write.

    Returns (added, changed, deleted) counts.
    """
    from llmdocs.indexing import (DocumentChunker, DocumentIndexer,
                                  DocumentParser, FileHasher)
    from llmdocs.llms_txt import generate_llms_txt
    from llmdocs.models import Chunk as ChunkModel

    parser = DocumentParser()
    chunker = DocumentChunker(max_chunk_tokens=cfg.search.chunk_size)
    hasher = FileHasher()
    indexer = DocumentIndexer(data_dir=data, embeddings_config=cfg.embeddings)

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

    all_docs = parser.load_all(cfg.docs_dir)
    cfg.llms_txt.output_path.write_text(generate_llms_txt(all_docs), encoding="utf-8")

    return len(added), len(changed), len(deleted)


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

    cfg = Config.load(_require_config(config_path))
    data = Path(data_dir)
    data.mkdir(parents=True, exist_ok=True)

    click.echo(f"Indexing {cfg.docs_dir}...")
    added, changed, deleted = _index_docs(cfg, data)
    click.echo(f"Done — {added} added, {changed} updated, {deleted} removed.")
    click.echo(f"Written {cfg.llms_txt.output_path}")


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


@cli.command("watch")
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
def watch(config_path: str, data_dir: str) -> None:
    """Watch docs directory and rebuild index on any markdown change."""
    import threading
    import time

    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    from llmdocs.config import Config

    cfg = Config.load(_require_config(config_path))
    data = Path(data_dir)
    data.mkdir(parents=True, exist_ok=True)

    pending = threading.Event()

    class _Handler(FileSystemEventHandler):
        def on_any_event(self, event) -> None:  # type: ignore[override]
            if not event.is_directory and str(event.src_path).endswith(".md"):
                pending.set()

    observer = Observer()
    observer.schedule(_Handler(), str(cfg.docs_dir), recursive=True)
    observer.start()
    click.echo(f"Watching {cfg.docs_dir} ... (Ctrl+C to stop)")

    try:
        while True:
            pending.wait()
            pending.clear()
            time.sleep(0.3)  # debounce: let burst of saves settle
            click.echo(f"[change detected] reindexing...")
            added, changed, deleted = _index_docs(cfg, data)
            click.echo(f"  {added} added, {changed} updated, {deleted} removed.")
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()


@cli.command("search")
@click.argument("query")
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
@click.option(
    "--limit", default=5, show_default=True, help="Maximum results to return."
)
def search_cmd(query: str, config_path: str, data_dir: str, limit: int) -> None:
    """Search the docs index from the terminal."""
    from llmdocs.config import Config
    from llmdocs.indexing import DocumentIndexer
    from llmdocs.indexing.search import HybridSearchEngine

    cfg = Config.load(_require_config(config_path))
    data = Path(data_dir)

    indexer = DocumentIndexer(data_dir=data, embeddings_config=cfg.embeddings)
    engine = HybridSearchEngine(
        indexer=indexer,
        semantic_weight=cfg.search.semantic_weight,
        keyword_weight=cfg.search.keyword_weight,
    )

    hits = engine.search(query, limit=limit)
    if not hits:
        click.echo("No results found.")
        return

    for i, hit in enumerate(hits, 1):
        click.echo(f"\n{i}. {hit.title}  (score: {hit.score:.3f})")
        click.echo(f"   {hit.url}")
        if hit.description:
            click.echo(f"   {hit.description}")
