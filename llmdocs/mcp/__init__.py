"""MCP subpackage — FastMCP server singleton and tool registrations for llmdocs."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastmcp import FastMCP
from fastmcp.dependencies import Depends

from llmdocs.mcp.runtime import LlmdocsRuntime
from llmdocs.mcp.tools import tool_get_doc, tool_list_docs, tool_search_docs

runtime = LlmdocsRuntime()
mcp = FastMCP("llmdocs")


def _get_runtime() -> LlmdocsRuntime:
    return runtime


@mcp.tool
def search_docs(
    query: str,
    limit: int = 5,
    rt: LlmdocsRuntime = Depends(_get_runtime),
) -> Dict[str, Any]:
    """Hybrid search over indexed chunks (semantic + keyword)."""
    return tool_search_docs(rt, query, limit)


@mcp.tool
def get_doc(
    path: str,
    rt: LlmdocsRuntime = Depends(_get_runtime),
) -> Dict[str, Any]:
    """Return full document body (no frontmatter) and metadata."""
    return tool_get_doc(rt, path)


@mcp.tool
def list_docs(
    category: Optional[str] = None,
    path: str = "/",
    rt: LlmdocsRuntime = Depends(_get_runtime),
) -> Dict[str, Any]:
    """List documents under the docs tree, optionally filtered by category and path prefix."""
    return tool_list_docs(rt, category, path)


__all__ = ["mcp", "runtime"]
