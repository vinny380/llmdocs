"""Tests for ChromaDB indexing."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from llmdocs.config import Config
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


# ── empty chunk filtering ─────────────────────────────────────────────────


def test_index_chunks_filters_empty_content(tmp_path: Path) -> None:
    """Chunks with empty/whitespace content are silently dropped."""
    chunks = [
        Chunk(
            chunk_id="a_chunk0",
            doc_path="/a.md",
            title_hierarchy=["A"],
            content="Real content here.",
            url="/a.md",
            metadata={"category": "General"},
        ),
        Chunk(
            chunk_id="a_chunk1",
            doc_path="/a.md",
            title_hierarchy=["A", "Empty"],
            content="",
            url="/a.md#empty",
            metadata={"category": "General"},
        ),
        Chunk(
            chunk_id="a_chunk2",
            doc_path="/a.md",
            title_hierarchy=["A", "Whitespace"],
            content="   \n  ",
            url="/a.md#whitespace",
            metadata={"category": "General"},
        ),
    ]
    indexer = DocumentIndexer(data_dir=tmp_path)
    indexer.index_chunks(chunks)
    assert indexer.collection.count() == 1


def test_index_chunks_all_empty_is_noop(tmp_path: Path) -> None:
    """If every chunk is empty, nothing is indexed and no API call is made."""
    chunks = [
        Chunk(
            chunk_id="b_chunk0",
            doc_path="/b.md",
            title_hierarchy=["B"],
            content="",
            url="/b.md",
            metadata={"category": "General"},
        ),
    ]
    indexer = DocumentIndexer(data_dir=tmp_path)
    indexer.index_chunks(chunks)
    assert indexer.collection.count() == 0


def test_index_chunks_openai_never_sees_empty_strings(tmp_path: Path) -> None:
    """With openai provider, empty chunks are filtered before the API call."""
    emb_cfg = Config.EmbeddingsConfig(
        provider="openai",
        model="text-embedding-3-small",
        api_key="sk-test",
    )

    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1] * 384

    mock_response = MagicMock()
    mock_response.data = [mock_embedding]

    with patch("openai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        indexer = DocumentIndexer(data_dir=tmp_path, embeddings_config=emb_cfg)
        indexer.index_chunks([
            Chunk(
                chunk_id="c_chunk0",
                doc_path="/c.md",
                title_hierarchy=["C"],
                content="Real content.",
                url="/c.md",
                metadata={"category": "General"},
            ),
            Chunk(
                chunk_id="c_chunk1",
                doc_path="/c.md",
                title_hierarchy=["C"],
                content="",
                url="/c.md#empty",
                metadata={"category": "General"},
            ),
        ])

    texts_sent = mock_client.embeddings.create.call_args[1]["input"]
    assert "" not in texts_sent
    assert len(texts_sent) == 1
    assert texts_sent[0] == "Real content."


# ── openai provider ───────────────────────────────────────────────────────


def test_indexer_openai_provider(tmp_path: Path, sample_chunks: list[Chunk]) -> None:
    """OpenAI provider dispatches to the openai client, not SentenceTransformer."""
    emb_cfg = Config.EmbeddingsConfig(
        provider="openai",
        model="text-embedding-3-small",
        api_key="sk-test",
        base_url="http://localhost:4000",
    )

    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1] * 384

    mock_response = MagicMock()
    mock_response.data = [mock_embedding] * len(sample_chunks)

    with patch("openai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        indexer = DocumentIndexer(
            data_dir=tmp_path, embeddings_config=emb_cfg
        )
        indexer.index_chunks(sample_chunks)

    mock_openai_cls.assert_called_once_with(
        api_key="sk-test", base_url="http://localhost:4000"
    )
    mock_client.embeddings.create.assert_called_once()
    call_kwargs = mock_client.embeddings.create.call_args
    assert call_kwargs[1]["model"] == "text-embedding-3-small"
    assert indexer.collection.count() == 2


def test_indexer_openai_does_not_import_sentence_transformers(
    tmp_path: Path,
) -> None:
    """When provider is 'openai', sentence_transformers is never imported."""
    emb_cfg = Config.EmbeddingsConfig(
        provider="openai",
        model="text-embedding-3-small",
        api_key="sk-test",
    )

    with patch("openai.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        with patch(
            "llmdocs.indexing.indexer.DocumentIndexer._init_local"
        ) as mock_local:
            DocumentIndexer(data_dir=tmp_path, embeddings_config=emb_cfg)
            mock_local.assert_not_called()
