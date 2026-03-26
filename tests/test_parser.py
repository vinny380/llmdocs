"""Tests for frontmatter parsing."""

from pathlib import Path

import pytest

from llmdocs.parser import DocumentParser


@pytest.fixture
def sample_doc_path(tmp_path: Path) -> Path:
    """Create a sample document."""
    doc = tmp_path / "getting-started.md"
    doc.write_text(
        """---
title: "Getting Started"
description: "Setup and installation guide"
category: "Quickstart"
tags: [tutorial, setup]
order: 1
---

# Getting Started

Welcome to llmdocs!

## Installation

Run `pip install llmdocs`.
""",
        encoding="utf-8",
    )
    return doc


def test_parse_document_with_frontmatter(sample_doc_path: Path) -> None:
    """Test parsing document with valid frontmatter."""
    parser = DocumentParser()
    doc = parser.parse(sample_doc_path, base_dir=sample_doc_path.parent)

    assert doc.title == "Getting Started"
    assert doc.description == "Setup and installation guide"
    assert doc.metadata.category == "Quickstart"
    assert doc.metadata.tags == ["tutorial", "setup"]
    assert doc.metadata.order == 1
    assert "# Getting Started" in doc.content
    assert "---" not in doc.content


def test_parse_document_without_frontmatter(tmp_path: Path) -> None:
    """Test parsing document without frontmatter (use fallbacks)."""
    doc_path = tmp_path / "no-frontmatter.md"
    doc_path.write_text("# My Document\n\nThis is the first paragraph.", encoding="utf-8")

    parser = DocumentParser()
    doc = parser.parse(doc_path, base_dir=tmp_path)

    assert doc.title == "My Document"
    assert doc.description == "This is the first paragraph."
    assert doc.metadata.category == "General"


def test_parse_document_invalid_frontmatter(tmp_path: Path) -> None:
    """Test parsing document with invalid frontmatter (graceful fallback)."""
    doc_path = tmp_path / "invalid.md"
    doc_path.write_text(
        """---
invalid yaml: [broken
---

# Document Title

Content here.
""",
        encoding="utf-8",
    )

    parser = DocumentParser()
    doc = parser.parse(doc_path, base_dir=tmp_path)

    assert doc.title == "Document Title"
    assert doc.content == "# Document Title\n\nContent here.\n"


def test_load_all_documents(tmp_path: Path) -> None:
    """Test loading all documents from directory."""
    (tmp_path / "doc1.md").write_text("# Doc 1\n\nContent 1", encoding="utf-8")
    (tmp_path / "doc2.md").write_text("# Doc 2\n\nContent 2", encoding="utf-8")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "doc3.md").write_text("# Doc 3\n\nContent 3", encoding="utf-8")

    parser = DocumentParser()
    docs = parser.load_all(tmp_path)

    assert len(docs) == 3
    titles = [d.title for d in docs]
    assert "Doc 1" in titles
    assert "Doc 2" in titles
    assert "Doc 3" in titles
