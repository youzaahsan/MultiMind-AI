import re
from dataclasses import dataclass, field
from typing import Dict, List, Set
from app.utils.logging import get_logger

logger = get_logger("entities")

@dataclass
class Entity:
    name: str
    category: str  # Concept, Model, Metric, Technology, Dataset, Organization
    occurrences: int = 1
    metadata: Dict[str, str] = field(default_factory=dict)

# Domain vocabulary for tech / AI / ML / Business
KNOWN_ENTITIES = {
    "neural network": "Concept",
    "supervised learning": "Concept",
    "unsupervised learning": "Concept",
    "reinforcement learning": "Concept",
    "deep learning": "Concept",
    "transformer": "Model",
    "rag": "Technology",
    "chromadb": "Technology",
    "fastapi": "Technology",
    "langchain": "Technology",
    "langgraph": "Technology",
    "scikit-learn": "Technology",
    "pandas": "Technology",
    "numpy": "Technology",
    "sqlite": "Technology",
    "postgresql": "Technology",
    "revenue": "Metric",
    "profit": "Metric",
    "profit margin": "Metric",
    "accuracy": "Metric",
    "precision": "Metric",
    "recall": "Metric",
    "f1-score": "Metric",
    "mae": "Metric",
    "rmse": "Metric",
    "pydantic": "Technology",
    "python": "Technology",
    "docker": "Technology",
    "agent": "Concept",
    "workflow": "Concept",
}

class EntityExtractor:
    """Extracts entities and categories from text chunks."""

    def extract(self, text: str) -> List[Entity]:
        entities: Dict[str, Entity] = {}
        text_lower = text.lower()

        # 1. Match known domain vocabulary
        for name, category in KNOWN_ENTITIES.items():
            pattern = rf"\b{re.escape(name)}\b"
            matches = len(re.findall(pattern, text_lower))
            if matches > 0:
                entities[name] = Entity(name=name.title(), category=category, occurrences=matches)

        # 2. Match Title Case noun phrases or CamelCase words (e.g. "Gradient Boosting", "Pydantic", "FastAPI")
        words = re.findall(r"\b[A-Z][a-zA-Z0-9_]{3,}\b", text)
        stop_words = {"This", "That", "There", "What", "When", "Where", "With", "From", "Into", "Over", "Also"}
        for word in words:
            if word not in stop_words and word.lower() not in entities:
                entities[word.lower()] = Entity(
                    name=word,
                    category="Technology" if word[0].isupper() and any(c.isupper() for c in word[1:]) else "Concept",
                    occurrences=text.count(word),
                )

        # 3. Match Acronyms (e.g. "API", "KPI", "RAG", "LLM", "CNN", "RNN", "ROC", "AUC")
        acronyms = re.findall(r"\b[A-Z]{2,6}\b", text)
        for acr in acronyms:
            if acr.lower() not in entities and acr not in ["THE", "AND", "FOR"]:
                entities[acr.lower()] = Entity(name=acr, category="Technology", occurrences=text.count(acr))

        return list(entities.values())
