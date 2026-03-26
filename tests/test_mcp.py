"""Tests for /mcp JSON routes."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_search_docs(test_client: TestClient) -> None:
    r = test_client.post("/mcp/search_docs", json={"query": "guide", "limit": 3})
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert isinstance(data["results"], list)


def test_get_doc(test_client: TestClient) -> None:
    r = test_client.post("/mcp/get_doc", json={"path": "/guide.md"})
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Guide"
    assert "This is a guide" in data["content"]
    assert data["url"] == "/guide.md"
    assert "category" in data["metadata"]


def test_get_doc_not_found(test_client: TestClient) -> None:
    r = test_client.post("/mcp/get_doc", json={"path": "/missing.md"})
    assert r.status_code == 404


def test_get_doc_path_traversal(test_client: TestClient) -> None:
    r = test_client.post("/mcp/get_doc", json={"path": "/../etc/passwd"})
    assert r.status_code == 400


def test_list_docs(test_client: TestClient) -> None:
    r = test_client.post("/mcp/list_docs", json={})
    assert r.status_code == 200
    data = r.json()
    paths = {d["path"] for d in data["documents"]}
    assert "/index.md" in paths
    assert "/guide.md" in paths


def test_list_docs_filter_category(test_client: TestClient) -> None:
    r = test_client.post("/mcp/list_docs", json={"category": "Tutorial"})
    assert r.status_code == 200
    docs = r.json()["documents"]
    assert len(docs) == 1
    assert docs[0]["path"] == "/guide.md"
