"""Frontmatter parsing and document loading."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List

import frontmatter

from llmdocs.models import Document, DocumentMetadata

logger = logging.getLogger(__name__)


def _strip_yaml_frontmatter_block(raw: str) -> str:
    """Remove a leading --- ... --- frontmatter block if present."""
    if not raw.startswith("---"):
        return raw
    parts = raw.split("---", 2)
    if len(parts) >= 3:
        return parts[2].lstrip("\n")
    return raw


def _rel_url_path(file_path: Path, base_dir: Path) -> str:
    rel = file_path.relative_to(base_dir)
    return "/" + rel.as_posix()


class DocumentParser:
    """Parser for markdown documents with frontmatter."""

    def parse(self, file_path: Path, base_dir: Path) -> Document:
        """Parse a single markdown file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                post = frontmatter.load(f)

            metadata_dict = dict(post.metadata)
            content = post.content

            title = metadata_dict.get("title")
            if not title:
                match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                title = match.group(1).strip() if match else file_path.stem

            description = metadata_dict.get("description", "") or ""
            if not description:
                paragraphs = [
                    p.strip()
                    for p in content.split("\n\n")
                    if p.strip() and not p.strip().startswith("#")
                ]
                description = paragraphs[0] if paragraphs else ""

            meta_kw = {
                k: v
                for k, v in metadata_dict.items()
                if k in DocumentMetadata.model_fields and k not in ("title", "description")
            }
            try:
                metadata = DocumentMetadata.model_validate(meta_kw)
            except Exception as e:  # noqa: BLE001 — invalid types in YAML
                logger.warning("Metadata validation failed for %s: %s", file_path, e)
                metadata = DocumentMetadata()

            rel_path = _rel_url_path(file_path, base_dir)

            return Document(
                path=rel_path,
                title=str(title),
                description=str(description),
                content=content,
                metadata=metadata,
            )

        except Exception as e:  # noqa: BLE001 — graceful fallback per design
            logger.warning("Error parsing %s: %s. Using fallbacks.", file_path, e)
            raw = file_path.read_text(encoding="utf-8")
            content = _strip_yaml_frontmatter_block(raw)

            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = match.group(1).strip() if match else file_path.stem

            paragraphs = [
                p.strip()
                for p in content.split("\n\n")
                if p.strip() and not p.strip().startswith("#")
            ]
            description = paragraphs[0] if paragraphs else ""

            rel_path = _rel_url_path(file_path, base_dir)

            return Document(
                path=rel_path,
                title=title,
                description=description,
                content=content,
                metadata=DocumentMetadata(),
            )

    def load_all(self, docs_dir: Path) -> List[Document]:
        """Load all markdown documents from directory (recursive)."""
        documents: List[Document] = []
        for md_file in sorted(docs_dir.rglob("*.md")):
            if md_file.is_file():
                documents.append(self.parse(md_file, base_dir=docs_dir))
        return documents
