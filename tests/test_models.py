"""Tests for data models."""

from datetime import datetime

from llmdocs.models import Chunk, Document, DocumentMetadata, SearchResult


def test_document_creation() -> None:
    """Test Document model creation."""
    doc = Document(
        path="/getting-started.md",
        title="Getting Started",
        description="Setup guide",
        content="# Getting Started\n\nWelcome!",
        metadata=DocumentMetadata(
            category="Quickstart",
            tags=["tutorial", "setup"],
            order=1,
        ),
    )

    assert doc.path == "/getting-started.md"
    assert doc.title == "Getting Started"
    assert doc.metadata.category == "Quickstart"
    assert doc.metadata.order == 1


def test_chunk_creation() -> None:
    """Test Chunk model creation."""
    chunk = Chunk(
        chunk_id="doc1_chunk0",
        doc_path="/getting-started.md",
        title_hierarchy=["Getting Started", "Installation"],
        content="Run pip install llmdocs",
        url="/getting-started.md#installation",
        metadata={"section": "Installation"},
    )

    assert chunk.chunk_id == "doc1_chunk0"
    assert chunk.title_hierarchy == ["Getting Started", "Installation"]
    assert "pip install" in chunk.content


def test_search_result_creation() -> None:
    """Test SearchResult model creation."""
    result = SearchResult(
        title="Getting Started",
        description="Setup guide",
        content_chunk="Run pip install llmdocs",
        url="/getting-started.md#installation",
        score=0.95,
    )

    assert result.title == "Getting Started"
    assert result.score == 0.95
    assert result.url == "/getting-started.md#installation"


def test_document_metadata_defaults() -> None:
    """Test DocumentMetadata with defaults."""
    metadata = DocumentMetadata(category="Guide")

    assert metadata.category == "Guide"
    assert metadata.tags == []
    assert metadata.order == 999
    assert metadata.status == "stable"


def test_document_get_url() -> None:
    """Document URL helper matches path."""
    doc = Document(
        path="/a.md",
        title="A",
        description="",
        content="# A",
    )
    assert doc.get_url() == "/a.md"
