"""Tests for document chunking."""

import pytest

from llmdocs.indexing import DocumentChunker
from llmdocs.models import Document, DocumentMetadata


@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing."""
    content = """# Getting Started

Welcome to llmdocs! This is the introduction.

## Installation

To install llmdocs, run the following command:

```bash
pip install llmdocs
```

## Configuration

Create a `llmdocs.yaml` file with the following content:

```yaml
docs_dir: ./docs
```

## Usage

Start the server with:

```bash
llmdocs serve
```
"""
    return Document(
        path="/getting-started.md",
        title="Getting Started",
        description="Setup guide",
        content=content,
        metadata=DocumentMetadata(category="Quickstart"),
    )


def test_chunk_by_h2_headers(sample_document: Document) -> None:
    """Test chunking by H2 headers."""
    chunker = DocumentChunker(max_chunk_tokens=500)
    chunks = chunker.chunk(sample_document)

    assert len(chunks) >= 3

    install_chunk = next(c for c in chunks if "Installation" in c.title_hierarchy)
    assert install_chunk.doc_path == "/getting-started.md"
    assert "Getting Started" in install_chunk.title_hierarchy
    assert "Installation" in install_chunk.title_hierarchy
    assert "pip install" in install_chunk.content
    assert install_chunk.url == "/getting-started.md#installation"


def test_chunk_large_section_recursively() -> None:
    """Test recursive chunking for sections > max_chunk_tokens."""
    large_content = "# Title\n\n## Section\n\n" + ("Long paragraph. " * 200)
    doc = Document(
        path="/large.md",
        title="Large Doc",
        content=large_content,
    )

    chunker = DocumentChunker(max_chunk_tokens=100)
    chunks = chunker.chunk(doc)

    assert len(chunks) > 1

    for chunk in chunks:
        token_count = chunker.count_tokens(chunk.content)
        assert token_count <= 150


def test_chunk_with_h3_subsections() -> None:
    """Test chunking with H3 subsections."""
    content = """# Main Title

## Section 1

Intro to section 1.

### Subsection 1.1

Content for subsection 1.1.

### Subsection 1.2

Content for subsection 1.2.
"""
    doc = Document(path="/doc.md", title="Main Title", content=content)

    chunker = DocumentChunker(max_chunk_tokens=50)
    chunks = chunker.chunk(doc)

    h3_chunks = [c for c in chunks if len(c.title_hierarchy) == 3]
    assert len(h3_chunks) >= 2

    subsection_chunk = h3_chunks[0]
    assert subsection_chunk.title_hierarchy[0] == "Main Title"
    assert subsection_chunk.title_hierarchy[1] == "Section 1"
    assert "Subsection" in subsection_chunk.title_hierarchy[2]


def test_chunk_empty_content_returns_no_chunks() -> None:
    """A document with whitespace-only content produces zero chunks."""
    doc = Document(path="/empty.md", title="Empty", content="   \n\n  ")
    chunker = DocumentChunker()
    assert chunker.chunk(doc) == []


def test_chunk_frontmatter_only_returns_no_chunks() -> None:
    """A document whose content is just a heading with no body produces no empty chunks."""
    doc = Document(path="/heading.md", title="Title", content="# Title\n\n")
    chunker = DocumentChunker()
    chunks = chunker.chunk(doc)
    for c in chunks:
        assert c.content.strip(), f"chunk {c.chunk_id} has empty content"


def test_chunk_empty_h2_section_filtered() -> None:
    """H2 sections with no body text are filtered out."""
    content = "# Doc\n\n## Empty Section\n\n## Real Section\n\nSome content here."
    doc = Document(path="/mixed.md", title="Doc", content=content)
    chunker = DocumentChunker()
    chunks = chunker.chunk(doc)
    for c in chunks:
        assert c.content.strip(), f"chunk {c.chunk_id} has empty content"
    assert any("Some content" in c.content for c in chunks)


def test_generate_chunk_id() -> None:
    """Test chunk ID generation."""
    doc = Document(path="/getting-started.md", title="Title", content="# Content")

    chunker = DocumentChunker()
    chunks = chunker.chunk(doc)

    for i, chunk in enumerate(chunks):
        assert chunk.chunk_id.startswith("/getting-started.md_chunk")
        assert str(i) in chunk.chunk_id
