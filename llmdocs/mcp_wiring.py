"""Thin callables that bind ``LlmdocsRuntime`` for FastMCP (requires real functions, not partials)."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from llmdocs.mcp_runtime import LlmdocsRuntime
from llmdocs.mcp_tools import tool_get_doc, tool_list_docs, tool_search_docs


def make_search_docs_tool(runtime: LlmdocsRuntime) -> Callable[..., Dict[str, Any]]:
    def search_docs(query: str, limit: int = 5) -> Dict[str, Any]:
        return tool_search_docs(runtime, query, limit)

    search_docs.__doc__ = tool_search_docs.__doc__
    search_docs.__name__ = "search_docs"
    return search_docs


def make_get_doc_tool(runtime: LlmdocsRuntime) -> Callable[..., Dict[str, Any]]:
    def get_doc(path: str) -> Dict[str, Any]:
        return tool_get_doc(runtime, path)

    get_doc.__doc__ = tool_get_doc.__doc__
    get_doc.__name__ = "get_doc"
    return get_doc


def make_list_docs_tool(runtime: LlmdocsRuntime) -> Callable[..., Dict[str, Any]]:
    def list_docs(category: Optional[str] = None, path: str = "/") -> Dict[str, Any]:
        return tool_list_docs(runtime, category, path)

    list_docs.__doc__ = tool_list_docs.__doc__
    list_docs.__name__ = "list_docs"
    return list_docs
