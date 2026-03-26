"""Hybrid search engine (semantic + keyword)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np
from rank_bm25 import BM25Okapi

from llmdocs.indexing.indexer import DocumentIndexer
from llmdocs.models import SearchResult

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """Hybrid search combining dense retrieval (Chroma) and BM25."""

    def __init__(
        self,
        indexer: DocumentIndexer,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> None:
        self.indexer = indexer
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight

        self.doc_ids: List[str] = []
        self.doc_contents: List[str] = []
        self.doc_metadatas: List[Any] = []
        self.bm25: BM25Okapi | None = None

        self._build_bm25_index()

    def _build_bm25_index(self) -> None:
        """Rebuild BM25 corpus from the current Chroma collection."""
        results = self.indexer.collection.get(include=["documents", "metadatas"])

        self.doc_ids = list(results.get("ids") or [])
        docs = results.get("documents") or []
        metas = results.get("metadatas") or []

        self.doc_contents = [d if d is not None else "" for d in docs]
        self.doc_metadatas = list(metas)

        tokenized = [doc.lower().split() for doc in self.doc_contents]
        if tokenized:
            self.bm25 = BM25Okapi(tokenized)
        else:
            self.bm25 = None

        logger.info("Built BM25 index with %s documents", len(self.doc_ids))

    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Hybrid search; returns `SearchResult` sorted by score descending."""
        if not query.strip():
            return []

        semantic_results = self.indexer.semantic_search(
            query, limit=max(limit * 2, limit)
        )
        keyword_results = self._bm25_search(query, limit=max(limit * 2, limit))

        combined: Dict[str, Dict[str, object]] = {}

        for row in semantic_results:
            doc_id = str(row["id"])
            dist = float(row.get("distance", 0.0))
            semantic_score = 1.0 / (1.0 + max(dist, 0.0))
            combined[doc_id] = {
                "semantic": semantic_score,
                "keyword": 0.0,
                "metadata": row.get("metadata") or {},
                "content": row.get("content") or "",
            }

        for doc_id, kw_score in keyword_results.items():
            if doc_id not in combined:
                idx = self.doc_ids.index(doc_id)
                combined[doc_id] = {
                    "semantic": 0.0,
                    "keyword": kw_score,
                    "metadata": self.doc_metadatas[idx] or {},
                    "content": self.doc_contents[idx],
                }
            else:
                entry = combined[doc_id]
                assert isinstance(entry, dict)
                entry["keyword"] = kw_score

        final: List[SearchResult] = []
        for doc_id, scores in combined.items():
            assert isinstance(scores, dict)
            sem = float(scores["semantic"])
            kw = float(scores["keyword"])
            final_score = sem * self.semantic_weight + kw * self.keyword_weight
            final_score = min(1.0, max(0.0, final_score))

            metadata = scores["metadata"]
            if not isinstance(metadata, dict):
                metadata = {}

            th_raw = metadata.get("title_hierarchy", "") or ""
            title_parts = [p for p in str(th_raw).split("|") if p.strip()]
            title = title_parts[0] if title_parts else "Untitled"
            description = str(metadata.get("description", "") or "")

            final.append(
                SearchResult(
                    title=title,
                    description=description,
                    content_chunk=str(scores["content"]),
                    url=str(metadata.get("url", "") or ""),
                    score=final_score,
                )
            )

        final.sort(key=lambda r: r.score, reverse=True)
        return final[:limit]

    def _bm25_search(self, query: str, limit: int) -> Dict[str, float]:
        """Return normalized BM25 scores keyed by chunk id."""
        if not self.bm25 or not self.doc_ids:
            return {}

        tokenized_query = query.lower().split()
        scores = np.asarray(self.bm25.get_scores(tokenized_query), dtype=float)
        if scores.size == 0:
            return {}

        max_score = float(np.max(scores))
        if max_score <= 0:
            return {}

        normalized = scores / max_score
        order = np.argsort(normalized)[::-1]

        out: Dict[str, float] = {}
        for idx in order[:limit]:
            if float(normalized[idx]) > 0:
                out[self.doc_ids[int(idx)]] = float(normalized[idx])
        return out

    def rebuild_index(self) -> None:
        """Reload BM25 after Chroma collection changes."""
        self._build_bm25_index()
