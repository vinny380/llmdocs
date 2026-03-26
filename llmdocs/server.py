"""FastAPI server for llmdocs."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, List

from fastapi import FastAPI, HTTPException, Request
from fastmcp.utilities.lifespan import combine_lifespans
from fastapi.responses import PlainTextResponse, Response

from llmdocs import __version__
from llmdocs.config import Config
from llmdocs.doc_paths import resolve_doc_path
from llmdocs.indexing import DocumentChunker, DocumentIndexer, DocumentParser, FileHasher, HybridSearchEngine
from llmdocs.llms_txt import generate_llms_txt, load_llms_txt
from llmdocs.mcp import mcp as mcp_server, runtime as mcp_runtime
from llmdocs.models import Chunk

logger = logging.getLogger(__name__)


def create_app(config: Config, data_dir: Path) -> FastAPI:
    """Create FastAPI app with startup indexing and health routes."""

    mcp_app = mcp_server.http_app(path="/")

    parser = DocumentParser()
    chunker = DocumentChunker(max_chunk_tokens=config.search.chunk_size)
    hasher = FileHasher()
    indexer = DocumentIndexer(
        data_dir=data_dir,
        embedding_model=config.embeddings.model,
    )

    @asynccontextmanager
    async def indexing_lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("Starting llmdocs server...")

        current_hashes = hasher.hash_directory(config.docs_dir)
        stored_hashes = indexer.get_all_hashes()
        changed, added, deleted = hasher.detect_changes(stored_hashes, current_hashes)

        if changed or added or deleted:
            logger.info(
                "Index update needed: %s changed, %s added, %s deleted",
                len(changed),
                len(added),
                len(deleted),
            )

            for doc_path in deleted:
                indexer.delete_by_doc_path(doc_path)

            docs_to_index = list(changed | added)
            if docs_to_index:
                all_docs = parser.load_all(config.docs_dir)
                docs_to_reindex = [d for d in all_docs if d.path in docs_to_index]

                for doc in docs_to_reindex:
                    doc.file_hash = current_hashes[doc.path]

                all_chunks: List[Chunk] = []
                for doc in docs_to_reindex:
                    if doc.path in changed:
                        indexer.delete_by_doc_path(doc.path)
                    chunks = chunker.chunk(doc)
                    for ch in chunks:
                        ch.metadata["file_hash"] = doc.file_hash
                    all_chunks.extend(chunks)

                if all_chunks:
                    indexer.index_chunks(all_chunks)

            logger.info("Index update finished")
        else:
            logger.info("Index is fresh, no update needed")

        search_engine = HybridSearchEngine(
            indexer=indexer,
            semantic_weight=config.search.semantic_weight,
            keyword_weight=config.search.keyword_weight,
        )
        app.state.indexer = indexer
        app.state.search_engine = search_engine
        app.state.parser = parser
        app.state.config = config
        app.state.mcp = mcp_server

        mcp_runtime.search_engine = search_engine
        mcp_runtime.parser = parser
        mcp_runtime.config = config

        logger.info("Server ready at http://%s:%s", config.server.host, config.server.port)

        yield

    app = FastAPI(
        title="llmdocs",
        description="Agent-first documentation platform",
        version=__version__,
        lifespan=combine_lifespans(indexing_lifespan, mcp_app.lifespan),
    )

    @app.get("/")
    async def root() -> dict[str, object]:
        return {
            "name": "llmdocs",
            "version": __version__,
            "description": "Agent-first documentation platform",
            "endpoints": {
                "health": "/health",
                "mcp": "Streamable HTTP MCP at /mcp (FastMCP tools: search_docs, get_doc, list_docs)",
                "raw_markdown": "GET /<path>.md (body without frontmatter)",
                "llms_txt": "/llms.txt",
                "docs": "/docs",
            },
        }

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "version": __version__}

    app.mount("/mcp", mcp_app)

    @app.get("/llms.txt")
    async def llms_txt_endpoint(request: Request) -> Response:
        """Serve llms.txt — manual override if configured, otherwise auto-generated."""
        cfg = request.app.state.config
        override = load_llms_txt(cfg.llms_txt.manual_override)
        if override is not None:
            return PlainTextResponse(content=override, media_type="text/plain; charset=utf-8")
        docs = request.app.state.parser.load_all(cfg.docs_dir)
        return PlainTextResponse(
            content=generate_llms_txt(docs),
            media_type="text/plain; charset=utf-8",
        )

    @app.get("/{path:path}")
    async def raw_markdown(path: str, request: Request) -> Response:
        """Serve markdown body only (no YAML frontmatter) at stable URL paths."""
        if not path.endswith(".md"):
            raise HTTPException(status_code=404, detail="Not found")

        config = request.app.state.config
        parser = request.app.state.parser
        url_path = path if path.startswith("/") else f"/{path}"
        fs_path = resolve_doc_path(config.docs_dir, url_path)
        doc = parser.parse(fs_path, base_dir=config.docs_dir)
        return PlainTextResponse(
            content=doc.content,
            media_type="text/markdown; charset=utf-8",
        )

    return app


def run_server(config: Config, data_dir: Path, watch: bool = False) -> None:
    """Run the server with uvicorn."""
    import uvicorn

    app = create_app(config, data_dir)
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        reload=watch,
    )
