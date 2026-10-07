import re
from typing import Any, Dict, List
from app.utils.logging import get_logger

logger = get_logger("reranker")

class Reranker:
    """
    Reranks candidate retrieved chunks using hybrid scoring:
    combining dense vector cosine similarity with lexical overlap,
    keyword density, and phrase match bonuses.
    """

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        query_terms = set(re.findall(r"\b\w{3,}\b", query.lower()))
        scored_candidates = []

        for item in candidates:
            content_lower = item.get("content", "").lower()
            orig_score = item.get("score", 0.0)

            # Lexical overlap score
            matched_terms = [t for t in query_terms if t in content_lower]
            lexical_ratio = len(matched_terms) / max(len(query_terms), 1)

            # Exact query phrase bonus
            phrase_bonus = 0.2 if query.lower() in content_lower else 0.0

            # Combined hybrid score (70% vector + 20% lexical + 10% phrase bonus)
            hybrid_score = (0.7 * orig_score) + (0.2 * lexical_ratio) + phrase_bonus

            scored_item = dict(item)
            scored_item["rerank_score"] = round(hybrid_score, 4)
            scored_candidates.append(scored_item)

        # Sort descending by rerank_score
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_candidates[:top_k]
