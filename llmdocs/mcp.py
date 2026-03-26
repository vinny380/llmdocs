"""FastMCP server factory for agent tools (search, get doc, list docs)."""

from __future__ import annotations

from fastmcp import FastMCP

from llmdocs.mcp_runtime import LlmdocsRuntime
from llmdocs.mcp_wiring import make_get_doc_tool, make_list_docs_tool, make_search_docs_tool


def create_mcp_server(runtime: LlmdocsRuntime) -> FastMCP:
    """Build a FastMCP server whose tools read from ``runtime`` (filled at startup)."""
    mcp = FastMCP("llmdocs")
    mcp.tool(make_search_docs_tool(runtime))
    mcp.tool(make_get_doc_tool(runtime))
    mcp.tool(make_list_docs_tool(runtime))
    return mcp


__all__ = ["LlmdocsRuntime", "create_mcp_server"]
