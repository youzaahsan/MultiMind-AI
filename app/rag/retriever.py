import re
from typing import Any, Dict, List, Optional, Tuple
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore, get_vector_store
from app.rag.reranker import Reranker
from app.config.settings import settings
from app.utils.logging import get_logger

logger = get_logger("retriever")

class RAGRetriever:
    """
    Orchestrates Query Preprocessing, Embedding, Vector Search,
    Metadata Filtering, Reranking, and Context Assembly.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        reranker: Optional[Reranker] = None,
    ):
        self.vector_store = vector_store or get_vector_store()
        self.embedding_service = embedding_service or EmbeddingService()
        self.reranker = reranker or Reranker()

    def preprocess_query(self, query: str) -> str:
        """Cleans and normalizes user query string."""
        cleaned = query.strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        document_id: Optional[str] = None,
        score_threshold: Optional[float] = None,
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Executes end-to-end retrieval.
        Returns:
            - matches: List of dicts with content, score, metadata
            - formatted_context: Consolidated context string for LLM
        """
        clean_query = self.preprocess_query(query)
        if not clean_query:
            return [], ""

        k = top_k or settings.TOP_K
        filter_meta = {"document_id": document_id} if document_id else None

        # 1. Embed query
        q_embedding = self.embedding_service.embed_text(clean_query)

        # 2. Vector search - retrieve extra candidates for reranking
        candidate_k = max(k * 2, 8)
        candidates = self.vector_store.similarity_search(
            query_embedding=q_embedding,
            top_k=candidate_k,
            score_threshold=score_threshold or settings.SIMILARITY_THRESHOLD,
            filter_metadata=filter_meta,
        )

        if not candidates:
            logger.info(f"No vector matches found for query: '{clean_query}'")
            return [], ""

        # 3. Rerank candidates
        reranked = self.reranker.rerank(clean_query, candidates, top_k=k)

        # 4. Construct context string
        context_blocks = []
        for i, doc in enumerate(reranked, start=1):
            meta = doc.get("metadata", {})
            fname = meta.get("filename", "unknown_document")
            page = meta.get("page", 1)
            section = meta.get("section", "General")
            modality = meta.get("modality", "text")
            body = doc.get("content", "").strip()

            block = (
                f"[Source {i}: {fname} | Page: {page} | Section: {section} | Modality: {modality}]\n"
                f"{body}"
            )
            context_blocks.append(block)

        formatted_context = "\n\n".join(context_blocks)
        return reranked, formatted_context
