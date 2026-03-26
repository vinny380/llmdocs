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
