import re
from dataclasses import dataclass
from typing import List, Tuple
from app.graph.entities import Entity

@dataclass
class Relationship:
    source: str
    target: str
    relation_type: str
    evidence_sentence: str
    weight: float = 1.0

# Predicate patterns mapping to canonical relation types
RELATION_PATTERNS = [
    (re.compile(r"\b(uses|utilizes|employs|applies)\b", re.I), "USES"),
    (re.compile(r"\b(implements|realizes|constructs)\b", re.I), "IMPLEMENTS"),
    (re.compile(r"\b(improves|enhances|optimizes|boosts)\b", re.I), "OPTIMIZES"),
    (re.compile(r"\b(evaluates|measures|benchmarks|tests)\b", re.I), "EVALUATES_ON"),
    (re.compile(r"\b(requires|depends on|relies on)\b", re.I), "DEPENDS_ON"),
    (re.compile(r"\b(is a|represents|is defined as|categorized as)\b", re.I), "IS_A"),
    (re.compile(r"\b(forecasts|predicts|projects)\b", re.I), "PREDICTS"),
    (re.compile(r"\b(contains|includes|consists of)\b", re.I), "CONTAINS"),
]

class RelationshipExtractor:
    """Extracts typed relationships between entities co-occurring in sentences."""

    def extract(self, text: str, entities: List[Entity]) -> List[Relationship]:
        if len(entities) < 2:
            return []

        relationships: List[Relationship] = []
        sentences = re.split(r"(?<=[.!?])\s+", text)
        entity_names = [e.name for e in entities]

        for sentence in sentences:
            sentence_lower = sentence.lower()
            # Find which entities appear in this sentence
            found_entities = [e for e in entity_names if e.lower() in sentence_lower]
            if len(found_entities) >= 2:
                # Pairwise relationships
                for i in range(len(found_entities)):
                    for j in range(i + 1, len(found_entities)):
                        src = found_entities[i]
                        tgt = found_entities[j]
                        rel_type = self._detect_relation_type(sentence)
                        relationships.append(Relationship(
                            source=src,
                            target=tgt,
                            relation_type=rel_type,
                            evidence_sentence=sentence.strip()[:200],
                            weight=1.0,
                        ))

        return relationships

    def _detect_relation_type(self, sentence: str) -> str:
        for pattern, rel_type in RELATION_PATTERNS:
            if pattern.search(sentence):
                return rel_type
        return "ASSOCIATED_WITH"
