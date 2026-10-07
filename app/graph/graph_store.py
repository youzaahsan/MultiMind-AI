import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import networkx as nx

from app.config.settings import settings
from app.graph.entities import Entity
from app.graph.relationships import Relationship
from app.utils.logging import get_logger

logger = get_logger("graph_store")

class KnowledgeGraphStore:
    """
    NetworkX-backed Knowledge Graph store managing entity nodes,
    relationship edges, multi-hop traversals, and JSON persistence.
    """

    def __init__(self, persistence_path: Optional[str] = None):
        self.persistence_path = Path(persistence_path or settings.VECTOR_DB_PATH) / "knowledge_graph.json"
        self.graph = nx.DiGraph()
        self._load()

    def add_entity(self, entity: Entity) -> None:
        """Adds or updates an entity node in the graph."""
        if not self.graph.has_node(entity.name):
            self.graph.add_node(
                entity.name,
                category=entity.category,
                occurrences=entity.occurrences,
                metadata=entity.metadata,
            )
        else:
            self.graph.nodes[entity.name]["occurrences"] = (
                self.graph.nodes[entity.name].get("occurrences", 0) + entity.occurrences
            )

    def add_relationship(self, rel: Relationship) -> None:
        """Adds a directed relationship between two entities."""
        if not self.graph.has_node(rel.source):
            self.graph.add_node(rel.source, category="Entity", occurrences=1)
        if not self.graph.has_node(rel.target):
            self.graph.add_node(rel.target, category="Entity", occurrences=1)

        self.graph.add_edge(
            rel.source,
            rel.target,
            relation_type=rel.relation_type,
            evidence=rel.evidence_sentence,
            weight=rel.weight,
        )

    def add_extracted_knowledge(self, entities: List[Entity], relationships: List[Relationship]) -> None:
        """Batch adds entities and relationships and persists."""
        for e in entities:
            self.add_entity(e)
        for r in relationships:
            self.add_relationship(r)
        self.save()

    def query_entity_subgraph(self, entity_name: str, max_depth: int = 2) -> Dict[str, Any]:
        """Traverses the neighborhood of an entity up to max_depth."""
        entity_match = self._find_matching_node(entity_name)
        if not entity_match:
            return {"nodes": [], "edges": []}

        nodes_visited: Set[str] = {entity_match}
        current_layer: Set[str] = {entity_match}

        for _ in range(max_depth):
            next_layer: Set[str] = set()
            for node in current_layer:
                successors = set(self.graph.successors(node))
                predecessors = set(self.graph.predecessors(node))
                neighbors = successors | predecessors
                next_layer |= (neighbors - nodes_visited)
            nodes_visited |= next_layer
            current_layer = next_layer
            if not current_layer:
                break

        sub = self.graph.subgraph(nodes_visited)
        nodes_data = [
            {"id": n, "label": n, "category": sub.nodes[n].get("category", "Concept")}
            for n in sub.nodes()
        ]
        edges_data = [
            {
                "source": u,
                "target": v,
                "relation": data.get("relation_type", "RELATED"),
                "evidence": data.get("evidence", ""),
            }
            for u, v, data in sub.edges(data=True)
        ]

        return {
            "root": entity_match,
            "nodes": nodes_data,
            "edges": edges_data,
        }

    def _find_matching_node(self, term: str) -> Optional[str]:
        term_clean = term.strip().lower()
        for node in self.graph.nodes():
            if str(node).lower() == term_clean or term_clean in str(node).lower():
                return node
        return None

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "density": round(nx.density(self.graph), 4) if self.graph.number_of_nodes() > 1 else 0.0,
        }

    def save(self) -> None:
        try:
            data = nx.node_link_data(self.graph)
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error persisting graph store: {e}")

    def _load(self) -> None:
        if self.persistence_path.exists():
            try:
                with open(self.persistence_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data)
                logger.info(f"Loaded Knowledge Graph with {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges.")
            except Exception as e:
                logger.warning(f"Could not load existing knowledge graph: {e}")


_graph_store_instance: Optional[KnowledgeGraphStore] = None

def get_graph_store() -> KnowledgeGraphStore:
    global _graph_store_instance
    if _graph_store_instance is None:
        _graph_store_instance = KnowledgeGraphStore()
    return _graph_store_instance
