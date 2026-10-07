import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from app.config.settings import settings
from app.utils.logging import get_logger

logger = get_logger("vector_store")

class VectorStore:
    """
    Vector database engine supporting cosine similarity search,
    metadata filtering, persistence, and chunk indexing.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or settings.VECTOR_DB_PATH)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "index.json"

        self.ids: List[str] = []
        self.vectors: Optional[np.ndarray] = None  # shape: (N, D)
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []

        self._load()

    def add_texts(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Adds a collection of text chunks and their embeddings into the store."""
        if not texts:
            return []

        import uuid
        count = len(texts)
        new_ids = ids if ids else [str(uuid.uuid4()) for _ in range(count)]
        new_metas = metadatas if metadatas else [{} for _ in range(count)]
        new_vectors = np.array(embeddings, dtype=np.float32)

        # Normalize incoming vectors
        norms = np.linalg.norm(new_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        new_vectors = new_vectors / norms

        if self.vectors is None or len(self.vectors) == 0:
            self.vectors = new_vectors
        else:
            self.vectors = np.vstack([self.vectors, new_vectors])

        self.ids.extend(new_ids)
        self.documents.extend(texts)
        self.metadatas.extend(new_metas)

        self._save()
        logger.info(f"Added {count} items to VectorStore. Total items: {len(self.ids)}")
        return new_ids

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs Cosine Similarity search with metadata filtering and thresholding.
        Returns sorted list of matches:
        [{"id": ..., "content": ..., "metadata": ..., "score": ...}]
        """
        if self.vectors is None or len(self.ids) == 0:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        # Cosine similarity is dot product of normalized vectors
        scores = np.dot(self.vectors, q_vec)

        # Rank indices descending
        ranked_indices = np.argsort(scores)[::-1]

        results: List[Dict[str, Any]] = []
        threshold = score_threshold if score_threshold is not None else settings.SIMILARITY_THRESHOLD

        for idx in ranked_indices:
            score = float(scores[idx])
            if score < threshold and len(results) > 0:
                continue

            meta = self.metadatas[idx]

            # Apply metadata filter if provided
            if filter_metadata:
                match = True
                for k, v in filter_metadata.items():
                    if meta.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            results.append({
                "id": self.ids[idx],
                "content": self.documents[idx],
                "metadata": meta,
                "score": round(score, 4),
            })

            if len(results) >= top_k:
                break

        return results

    def delete_by_document_id(self, document_id: str) -> int:
        """Removes all chunks associated with a specific document ID."""
        if not self.ids:
            return 0

        keep_indices = [
            i for i, meta in enumerate(self.metadatas)
            if meta.get("document_id") != document_id
        ]
        removed_count = len(self.ids) - len(keep_indices)

        if removed_count > 0:
            self.ids = [self.ids[i] for i in keep_indices]
            self.documents = [self.documents[i] for i in keep_indices]
            self.metadatas = [self.metadatas[i] for i in keep_indices]
            self.vectors = self.vectors[keep_indices] if len(keep_indices) > 0 else None
            self._save()
            logger.info(f"Removed {removed_count} vector chunks for document {document_id}")

        return removed_count

    def count(self) -> int:
        return len(self.ids)

    def _save(self) -> None:
        """Persists metadata, texts, and vectors to disk."""
        data = {
            "ids": self.ids,
            "documents": self.documents,
            "metadatas": self.metadatas,
        }
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        if self.vectors is not None:
            np.save(self.storage_dir / "vectors.npy", self.vectors)

    def _load(self) -> None:
        """Loads index from disk if present."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.ids = data.get("ids", [])
                    self.documents = data.get("documents", [])
                    self.metadatas = data.get("metadatas", [])

                vec_file = self.storage_dir / "vectors.npy"
                if vec_file.exists() and len(self.ids) > 0:
                    self.vectors = np.load(vec_file)
                logger.info(f"Loaded {len(self.ids)} items from vector index at {self.storage_dir}")
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")


# Singleton instance
_vector_store_instance: Optional[VectorStore] = None

def get_vector_store() -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
