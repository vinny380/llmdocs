"""Data models for llmdocs (internal — use the CLI, not these imports)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentMetadata(BaseModel):
    """Metadata extracted from frontmatter."""

    category: str = "General"
    tags: List[str] = Field(default_factory=list)
    order: int = 999
    prerequisites: List[Dict[str, str]] = Field(default_factory=list)
    related: List[str] = Field(default_factory=list)
    last_updated: Optional[datetime] = None
    status: str = "stable"
    aliases: List[str] = Field(default_factory=list)


class Document(BaseModel):
    """A documentation page."""

    path: str  # Relative path like /getting-started.md
    title: str
    description: str = ""
    content: str  # Markdown content without frontmatter
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    file_hash: Optional[str] = None  # SHA256 hash for freshness detection

    def get_url(self) -> str:
        """Get the URL for this document."""
        return self.path


class Chunk(BaseModel):
    """A searchable chunk of a document."""

    chunk_id: str  # Unique ID like "doc1_chunk0"
    doc_path: str  # Source document path
    title_hierarchy: List[str]  # ["Page Title", "H2 Section", "H3 Subsection"]
    content: str  # The actual chunk content
    url: str  # URL with anchor like /getting-started.md#installation
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None  # Vector embedding


class SearchResult(BaseModel):
    """A search result returned to users."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Getting Started",
                "description": "Setup and installation guide",
                "content_chunk": "Run pip install llmdocs to install...",
                "url": "/getting-started.md#installation",
                "score": 0.95,
            }
        }
    )

    title: str
    description: str
    content_chunk: str
    url: str
    score: float
