"""Tests for hybrid search."""

from pathlib import Path

import pytest

from llmdocs.indexer import DocumentIndexer
from llmdocs.models import Chunk
from llmdocs.search import HybridSearchEngine


@pytest.fixture
def search_engine(tmp_path: Path) -> HybridSearchEngine:
    """Create search engine with sample data."""
    indexer = DocumentIndexer(data_dir=tmp_path)

    chunks = [
        Chunk(
            chunk_id="doc1_chunk0",
            doc_path="/install.md",
            title_hierarchy=["Installation Guide"],
            content="To install llmdocs, run: pip install llmdocs",
            url="/install.md",
            metadata={"category": "Quickstart", "file_hash": "hash1"},
        ),
        Chunk(
            chunk_id="doc2_chunk0",
            doc_path="/config.md",
            title_hierarchy=["Configuration"],
            content="Configure llmdocs using llmdocs.yaml file",
            url="/config.md",
            metadata={"category": "Guide", "file_hash": "hash2"},
        ),
        Chunk(
            chunk_id="doc3_chunk0",
            doc_path="/api.md",
            title_hierarchy=["API Reference"],
            content="The API provides endpoints for searching documentation",
            url="/api.md",
            metadata={"category": "Reference", "file_hash": "hash3"},
        ),
    ]

    indexer.index_chunks(chunks)

    return HybridSearchEngine(
        indexer=indexer,
        semantic_weight=0.7,
        keyword_weight=0.3,
    )


def test_hybrid_search(search_engine: HybridSearchEngine) -> None:
    """Test hybrid search combining semantic and keyword."""
    results = search_engine.search("how to install llmdocs", limit=3)

    assert len(results) > 0
    assert results[0].url == "/install.md"
    assert "install" in results[0].content_chunk.lower()


def test_semantic_weight_prioritizes_meaning(search_engine: HybridSearchEngine) -> None:
    """Semantic search finds conceptually related content."""
    results = search_engine.search("setup guide", limit=2)
    assert any("install" in r.content_chunk.lower() for r in results)


def test_keyword_weight_prioritizes_exact_matches(search_engine: HybridSearchEngine) -> None:
    """Keyword search boosts exact matches."""
    results = search_engine.search("llmdocs.yaml", limit=2)
    assert results[0].url == "/config.md"


def test_search_result_format(search_engine: HybridSearchEngine) -> None:
    """Search results expose SearchResult fields and bounded score."""
    results = search_engine.search("installation", limit=1)

    assert len(results) == 1
    result = results[0]

    assert hasattr(result, "title")
    assert hasattr(result, "description")
    assert hasattr(result, "content_chunk")
    assert hasattr(result, "url")
    assert hasattr(result, "score")
    assert 0 <= result.score <= 1


def test_empty_query_returns_empty(search_engine: HybridSearchEngine) -> None:
    """Empty query returns no results."""
    results = search_engine.search("", limit=5)
    assert len(results) == 0


def test_rebuild_index(search_engine: HybridSearchEngine) -> None:
    """rebuild_index refreshes BM25 from Chroma."""
    search_engine.rebuild_index()
    assert search_engine.bm25 is not None
    assert len(search_engine.doc_ids) == 3
