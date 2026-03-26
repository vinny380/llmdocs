"""Tests for FastAPI server."""


def test_root_endpoint(test_client) -> None:
    """Test root endpoint returns info."""
    response = test_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_health_endpoint(test_client) -> None:
    """Test health check endpoint."""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_docs_endpoint_returns_openapi(test_client) -> None:
    """Test OpenAPI docs are available."""
    response = test_client.get("/docs")

    assert response.status_code == 200


def test_raw_markdown_strips_frontmatter(test_client) -> None:
    """GET /<doc>.md returns body without YAML frontmatter."""
    response = test_client.get("/guide.md")

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/markdown")
    body = response.text.strip()
    assert not body.startswith("---")
    assert body.startswith("# Guide")
    assert "This is a guide." in body


def test_raw_markdown_nested_path(test_client, sample_docs_dir) -> None:
    """Nested markdown files are served under the same URL shape as doc.path."""
    nested = sample_docs_dir / "nested"
    nested.mkdir()
    (nested / "page.md").write_text(
        "---\ntitle: Nested\n---\n\n# Nested Page\n",
        encoding="utf-8",
    )

    response = test_client.get("/nested/page.md")

    assert response.status_code == 200
    assert "# Nested Page" in response.text


def test_raw_markdown_not_found(test_client) -> None:
    response = test_client.get("/missing.md")
    assert response.status_code == 404


def test_raw_markdown_rejects_traversal(test_client) -> None:
    response = test_client.get("/../etc/passwd.md")
    assert response.status_code in (400, 404)


def test_non_md_path_not_raw_route(test_client) -> None:
    """Paths without .md are not served as markdown (avoid stealing /health, etc.)."""
    assert test_client.get("/health").status_code == 200
    assert test_client.get("/nothing-here").status_code == 404
