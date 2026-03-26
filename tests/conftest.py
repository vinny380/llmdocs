"""Shared test fixtures."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from llmdocs.config import Config
from llmdocs.server import create_app


@pytest.fixture
def sample_docs_dir(tmp_path: Path) -> Path:
    """Create sample docs directory."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "index.md").write_text(
        """---
title: "Home"
description: "Welcome"
---

# Home

Welcome to the docs!
""",
        encoding="utf-8",
    )

    (docs_dir / "guide.md").write_text(
        """---
title: "Guide"
category: "Tutorial"
---

# Guide

This is a guide.
""",
        encoding="utf-8",
    )

    return docs_dir


@pytest.fixture
def test_config(tmp_path: Path, sample_docs_dir: Path) -> Config:
    """Create test configuration."""
    return Config(
        docs_dir=sample_docs_dir,
        server=Config.ServerConfig(host="0.0.0.0", port=8080),
    )


@pytest.fixture
def test_client(test_config: Config, tmp_path: Path) -> TestClient:
    """Create test client (runs startup lifespan: indexing + embedding model load)."""
    app = create_app(config=test_config, data_dir=tmp_path / "data")
    return TestClient(app)
