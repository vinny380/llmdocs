"""ChromaDB indexing and embeddings."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from llmdocs.models import Chunk

logger = logging.getLogger(__name__)


def _chunk_metadata_for_chroma(chunk: Chunk) -> Dict[str, Any]:
    """Chroma metadata: str, int, float, or bool only."""
    meta: Dict[str, Any] = {
        "doc_path": chunk.doc_path,
        "url": chunk.url,
        "title_hierarchy": "|".join(chunk.title_hierarchy),
    }
    for key, val in chunk.metadata.items():
        if val is None:
            continue
        if isinstance(val, (str, int, float, bool)):
            meta[key] = val
        else:
            meta[key] = str(val)
    return meta


class DocumentIndexer:
    """Manages ChromaDB index for document chunks."""

    def __init__(
        self,
        data_dir: Path,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        collection_name: str = "llmdocs",
    ) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._collection_name = collection_name

        self.client = chromadb.PersistentClient(
            path=str(self.data_dir / "chroma"),
            settings=Settings(anonymized_telemetry=False),
        )

        logger.info("Loading embedding model: %s", embedding_model)
        self.embedding_model = SentenceTransformer(embedding_model)

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "llmdocs documentation chunks"},
        )

    def index_chunks(self, chunks: List[Chunk]) -> None:
        """Index a list of chunks (adds to the collection)."""
        if not chunks:
            return

        texts = [c.content for c in chunks]
        emb = self.embedding_model.encode(texts, show_progress_bar=False)
        embeddings = emb.tolist() if hasattr(emb, "tolist") else list(emb)

        ids = [c.chunk_id for c in chunks]
        metadatas = [_chunk_metadata_for_chroma(c) for c in chunks]

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info("Indexed %s chunks", len(chunks))

    def semantic_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Dense-vector search over indexed chunks."""
        qe = self.embedding_model.encode([query], show_progress_bar=False)
        query_embedding = qe.tolist()[0] if hasattr(qe, "tolist") else list(qe[0])

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )

        formatted: List[Dict[str, Any]] = []
        ids_list = results.get("ids") or [[]]
        docs_list = results.get("documents") or [[]]
        meta_list = results.get("metadatas") or [[]]
        dist_list = results.get("distances") or [[]]

        for i in range(len(ids_list[0])):
            dist = 0.0
            if dist_list and dist_list[0] and i < len(dist_list[0]):
                dist = float(dist_list[0][i])
            formatted.append(
                {
                    "id": ids_list[0][i],
                    "content": docs_list[0][i] if docs_list[0] else "",
                    "metadata": meta_list[0][i] if meta_list[0] else {},
                    "distance": dist,
                }
            )

        return formatted

    def get_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Return Chroma `get` result for one id, or None if missing."""
        try:
            result = self.collection.get(
                ids=[chunk_id],
                include=["documents", "metadatas"],
            )
            if not result.get("ids"):
                return None
            return result
        except Exception as e:  # noqa: BLE001
            logger.error("Error retrieving chunk %s: %s", chunk_id, e)
            return None

    def delete_by_doc_path(self, doc_path: str) -> None:
        """Delete all chunks whose metadata doc_path matches."""
        results = self.collection.get(
            where={"doc_path": doc_path},
            include=[],
        )
        if results.get("ids"):
            self.collection.delete(ids=results["ids"])
            logger.info("Deleted %s chunks from %s", len(results["ids"]), doc_path)

    def get_all_hashes(self) -> Dict[str, str]:
        """Map doc_path -> file_hash from stored chunk metadata."""
        results = self.collection.get(include=["metadatas"])
        metadatas = results.get("metadatas") or []
        hashes: Dict[str, str] = {}
        for m in metadatas:
            if not m:
                continue
            doc_path = m.get("doc_path")
            file_hash = m.get("file_hash")
            if doc_path is not None and file_hash is not None:
                hashes[str(doc_path)] = str(file_hash)
        return hashes

    def clear(self) -> None:
        """Remove all vectors in this collection (recreate empty collection)."""
        name = self._collection_name
        self.client.delete_collection(name)
        self.collection = self.client.get_or_create_collection(
            name=name,
            metadata={"description": "llmdocs documentation chunks"},
        )
        logger.info("Cleared index")
