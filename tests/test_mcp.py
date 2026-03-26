"""Tests for FastMCP tools (in-process client)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from fastmcp.client import Client


@pytest.mark.asyncio
async def test_search_docs(test_client: TestClient) -> None:
    mcp = test_client.app.state.mcp
    async with Client(mcp) as client:
        r = await client.call_tool("search_docs", {"query": "guide", "limit": 3})
    assert r.data is not None
    assert "results" in r.data
    assert isinstance(r.data["results"], list)


@pytest.mark.asyncio
async def test_get_doc(test_client: TestClient) -> None:
    mcp = test_client.app.state.mcp
    async with Client(mcp) as client:
        r = await client.call_tool("get_doc", {"path": "/guide.md"})
    assert r.data is not None
    assert r.data["title"] == "Guide"
    assert "This is a guide" in r.data["content"]
    assert r.data["url"] == "/guide.md"
    assert "category" in r.data["metadata"]


@pytest.mark.asyncio
async def test_get_doc_not_found(test_client: TestClient) -> None:
    mcp = test_client.app.state.mcp
    async with Client(mcp) as client:
        r = await client.call_tool(
            "get_doc",
            {"path": "/missing.md"},
            raise_on_error=False,
        )
    assert r.is_error


@pytest.mark.asyncio
async def test_get_doc_path_traversal(test_client: TestClient) -> None:
    mcp = test_client.app.state.mcp
    async with Client(mcp) as client:
        r = await client.call_tool(
            "get_doc",
            {"path": "/../etc/passwd"},
            raise_on_error=False,
        )
    assert r.is_error


@pytest.mark.asyncio
async def test_list_docs(test_client: TestClient) -> None:
    mcp = test_client.app.state.mcp
    async with Client(mcp) as client:
        r = await client.call_tool("list_docs", {})
    assert r.data is not None
    paths = {d["path"] for d in r.data["documents"]}
    assert "/index.md" in paths
    assert "/guide.md" in paths


@pytest.mark.asyncio
async def test_list_docs_filter_category(test_client: TestClient) -> None:
    mcp = test_client.app.state.mcp
    async with Client(mcp) as client:
        r = await client.call_tool("list_docs", {"category": "Tutorial"})
    assert r.data is not None
    docs = r.data["documents"]
    assert len(docs) == 1
    assert docs[0]["path"] == "/guide.md"
