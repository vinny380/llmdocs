"""FastMCP tools for agent access (search, get doc, list docs)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from llmdocs.config import Config
from llmdocs.doc_paths import resolve_doc_path
from llmdocs.parser import DocumentParser
from llmdocs.search import HybridSearchEngine


@dataclass
class LlmdocsRuntime:
    """Populated during FastAPI lifespan before MCP tools run."""

    search_engine: HybridSearchEngine | None = None
    parser: DocumentParser | None = None
    config: Config | None = None


def _tool_error_from_http(exc: HTTPException) -> ToolError:
    detail = exc.detail
    msg = detail if isinstance(detail, str) else str(detail)
    return ToolError(msg)


def create_mcp_server(runtime: LlmdocsRuntime) -> FastMCP:
    """Build a FastMCP server whose tools read from ``runtime`` (filled at startup)."""
    mcp = FastMCP("llmdocs")

    @mcp.tool()
    def search_docs(query: str, limit: int = 5) -> Dict[str, Any]:
        """Hybrid search over indexed chunks (semantic + keyword)."""
        if runtime.search_engine is None:
            raise ToolError("Search engine not initialized")
        hits = runtime.search_engine.search(query.strip(), limit=limit)
        return {
            "results": [
                {
                    "title": h.title,
                    "description": h.description,
                    "content_chunk": h.content_chunk,
                    "url": h.url,
                    "score": h.score,
                }
                for h in hits
            ]
        }

    @mcp.tool()
    def get_doc(path: str) -> Dict[str, Any]:
        """Return full document body (no frontmatter) and metadata."""
        if runtime.parser is None or runtime.config is None:
            raise ToolError("Document services not initialized")
        try:
            fs_path = resolve_doc_path(runtime.config.docs_dir, path)
        except HTTPException as e:
            raise _tool_error_from_http(e) from e
        doc = runtime.parser.parse(fs_path, base_dir=runtime.config.docs_dir)
        return {
            "title": doc.title,
            "description": doc.description,
            "content": doc.content,
            "url": doc.path,
            "metadata": doc.metadata.model_dump(),
        }

    @mcp.tool()
    def list_docs(
        category: Optional[str] = None,
        path: str = "/",
    ) -> Dict[str, Any]:
        """List documents under the docs tree, optionally filtered by category and path prefix."""
        if runtime.parser is None or runtime.config is None:
            raise ToolError("Document services not initialized")
        docs = runtime.parser.load_all(runtime.config.docs_dir)

        prefix = path.strip() or "/"
        if not prefix.startswith("/"):
            prefix = "/" + prefix

        out: List[Dict[str, str]] = []
        for d in docs:
            if category is not None and d.metadata.category != category:
                continue
            if prefix not in ("", "/") and not d.path.startswith(prefix):
                continue
            out.append(
                {
                    "title": d.title,
                    "description": d.description,
                    "path": d.path,
                    "category": d.metadata.category,
                }
            )

        out.sort(key=lambda x: (x["category"], x["path"]))
        return {"documents": out}

    return mcp
