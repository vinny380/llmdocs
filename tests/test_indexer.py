"""Tests for ChromaDB indexing."""

from pathlib import Path

import pytest

from llmdocs.indexing import DocumentIndexer
from llmdocs.models import Chunk


@pytest.fixture
def sample_chunks() -> list[Chunk]:
    """Create sample chunks for testing."""
    return [
        Chunk(
            chunk_id="doc1_chunk0",
            doc_path="/getting-started.md",
            title_hierarchy=["Getting Started", "Installation"],
            content="Run pip install llmdocs to install the package.",
            url="/getting-started.md#installation",
            metadata={"category": "Quickstart"},
        ),
        Chunk(
            chunk_id="doc1_chunk1",
            doc_path="/getting-started.md",
            title_hierarchy=["Getting Started", "Configuration"],
            content="Create llmdocs.yaml configuration file.",
            url="/getting-started.md#configuration",
            metadata={"category": "Quickstart"},
        ),
    ]


def test_index_creation(tmp_path: Path, sample_chunks: list[Chunk]) -> None:
    """Test creating an index from chunks."""
    indexer = DocumentIndexer(data_dir=tmp_path)

    indexer.index_chunks(sample_chunks)

    assert indexer.collection.count() == 2


def test_retrieve_by_id(tmp_path: Path, sample_chunks: list[Chunk]) -> None:
    """Test retrieving chunk by ID."""
    indexer = DocumentIndexer(data_dir=tmp_path)
    indexer.index_chunks(sample_chunks)

    result = indexer.get_by_id("doc1_chunk0")

    assert result is not None
    assert result["documents"][0] == sample_chunks[0].content


def test_semantic_search(tmp_path: Path, sample_chunks: list[Chunk]) -> None:
    """Test semantic search."""
    indexer = DocumentIndexer(data_dir=tmp_path)
    indexer.index_chunks(sample_chunks)

    results = indexer.semantic_search("how to install", limit=2)

    assert len(results) > 0
    assert any("install" in r["content"].lower() for r in results)


def test_get_all_hashes(tmp_path: Path, sample_chunks: list[Chunk]) -> None:
    """Test retrieving all stored file hashes."""
    for chunk in sample_chunks:
        chunk.metadata["file_hash"] = "hash123"

    indexer = DocumentIndexer(data_dir=tmp_path)
    indexer.index_chunks(sample_chunks)

    hashes = indexer.get_all_hashes()

    assert "/getting-started.md" in hashes
    assert hashes["/getting-started.md"] == "hash123"


def test_delete_by_doc_path(tmp_path: Path, sample_chunks: list[Chunk]) -> None:
    """Test deleting all chunks from a document."""
    indexer = DocumentIndexer(data_dir=tmp_path)
    indexer.index_chunks(sample_chunks)

    assert indexer.collection.count() == 2

    indexer.delete_by_doc_path("/getting-started.md")

    assert indexer.collection.count() == 0
