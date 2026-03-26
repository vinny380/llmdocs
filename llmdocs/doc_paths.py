"""Safe resolution of documentation paths on disk (API + HTTP)."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException


def resolve_doc_path(docs_root: Path, url_path: str) -> Path:
    """Resolve a URL-style path (e.g. ``/guide.md``) to a file under ``docs_root``."""
    raw = url_path.strip()
    if not raw.startswith("/"):
        raw = "/" + raw
    rel = raw.lstrip("/")
    if not rel or any(p == ".." for p in rel.split("/")):
        raise HTTPException(status_code=400, detail="Invalid document path")

    candidate = (docs_root / rel).resolve()
    base = docs_root.resolve()
    try:
        candidate.relative_to(base)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail="Path outside docs directory"
        ) from e

    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Document not found")
    if candidate.suffix.lower() != ".md":
        raise HTTPException(status_code=400, detail="Not a markdown file")
    return candidate
