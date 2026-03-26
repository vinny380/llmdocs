"""HTTP JSON routes for agent tools (MCP-aligned names under /mcp)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/mcp", tags=["mcp"])


class SearchDocsRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=100)


class SearchHit(BaseModel):
    title: str
    description: str
    content_chunk: str
    url: str
    score: float


class SearchDocsResponse(BaseModel):
    results: List[SearchHit]


class GetDocRequest(BaseModel):
    path: str = Field(..., description="Document path, e.g. /guide.md")


class GetDocResponse(BaseModel):
    title: str
    description: str
    content: str
    url: str
    metadata: dict[str, Any]


class ListDocsRequest(BaseModel):
    category: Optional[str] = None
    path: str = Field(default="/", description="Path prefix filter (default all)")


class ListDocItem(BaseModel):
    title: str
    description: str
    path: str
    category: str


class ListDocsResponse(BaseModel):
    documents: List[ListDocItem]


def _resolve_doc_path(docs_root: Path, url_path: str) -> Path:
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


@router.post("/search_docs", response_model=SearchDocsResponse)
async def search_docs(body: SearchDocsRequest, request: Request) -> SearchDocsResponse:
    """Hybrid search over indexed chunks (semantic + keyword)."""
    engine = request.app.state.search_engine
    hits = engine.search(body.query.strip(), limit=body.limit)
    return SearchDocsResponse(
        results=[
            SearchHit(
                title=h.title,
                description=h.description,
                content_chunk=h.content_chunk,
                url=h.url,
                score=h.score,
            )
            for h in hits
        ]
    )


@router.post("/get_doc", response_model=GetDocResponse)
async def get_doc(body: GetDocRequest, request: Request) -> GetDocResponse:
    """Return full document body (no frontmatter) and metadata."""
    config = request.app.state.config
    parser = request.app.state.parser
    path = _resolve_doc_path(config.docs_dir, body.path)
    doc = parser.parse(path, base_dir=config.docs_dir)
    return GetDocResponse(
        title=doc.title,
        description=doc.description,
        content=doc.content,
        url=doc.path,
        metadata=doc.metadata.model_dump(),
    )


@router.post("/list_docs", response_model=ListDocsResponse)
async def list_docs(body: ListDocsRequest, request: Request) -> ListDocsResponse:
    """List documents under docs_dir, optionally filtered by category and path prefix."""
    config = request.app.state.config
    parser = request.app.state.parser
    docs = parser.load_all(config.docs_dir)

    prefix = body.path.strip() or "/"
    if not prefix.startswith("/"):
        prefix = "/" + prefix

    out: List[ListDocItem] = []
    for d in docs:
        if body.category is not None and d.metadata.category != body.category:
            continue
        if prefix not in ("", "/") and not d.path.startswith(prefix):
            continue
        out.append(
            ListDocItem(
                title=d.title,
                description=d.description,
                path=d.path,
                category=d.metadata.category,
            )
        )

    out.sort(key=lambda x: (x.category, x.path))
    return ListDocsResponse(documents=out)
