"""MCP tool logic — pure functions called by the registered FastMCP tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from fastmcp.exceptions import ToolError

from llmdocs.doc_paths import resolve_doc_path
from llmdocs.mcp.runtime import LlmdocsRuntime


def _tool_error_from_http(exc: HTTPException) -> ToolError:
    detail = exc.detail
    msg = detail if isinstance(detail, str) else str(detail)
    return ToolError(msg)


def tool_search_docs(runtime: LlmdocsRuntime, query: str, limit: int = 5) -> Dict[str, Any]:
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


def tool_get_doc(runtime: LlmdocsRuntime, path: str) -> Dict[str, Any]:
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


def tool_list_docs(
    runtime: LlmdocsRuntime,
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
