from typing import Any, Dict, List, Optional, Tuple
from app.graph.graph_store import KnowledgeGraphStore, get_graph_store
from app.graph.entities import EntityExtractor
from app.rag.retriever import RAGRetriever
from app.utils.logging import get_logger

logger = get_logger("graph_retriever")

class GraphRAGRetriever:
    """
    Hybrid Graph + Vector Retriever:
    1. Extracts query entities
    2. Retrieves relational facts & subgraph paths from Knowledge Graph
    3. Retrieves dense semantic chunks from Vector Store
    4. Combines them into a multi-hop context
    """

    def __init__(
        self,
        graph_store: Optional[KnowledgeGraphStore] = None,
        vector_retriever: Optional[RAGRetriever] = None,
    ):
        self.graph_store = graph_store or get_graph_store()
        self.vector_retriever = vector_retriever or RAGRetriever()
        self.entity_extractor = EntityExtractor()

    def retrieve_hybrid(
        self,
        query: str,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """
        Executes dual graph + vector retrieval and returns consolidated context.
        """
        # 1. Vector Retrieval
        vector_docs, vector_context = self.vector_retriever.retrieve(query=query, top_k=top_k)

        # 2. Extract entities from query
        query_entities = self.entity_extractor.extract(query)
        graph_facts: List[str] = []
        subgraphs: List[Dict[str, Any]] = []

        # 3. Graph search for each identified entity
        for entity in query_entities:
            subgraph = self.graph_store.query_entity_subgraph(entity.name, max_depth=1)
            if subgraph["edges"]:
                subgraphs.append(subgraph)
                for edge in subgraph["edges"]:
                    graph_facts.append(
                        f"Relationship: [{edge['source']}] --({edge['relation']})--> [{edge['target']}]"
                    )

        # 4. Synthesize combined context
        combined_parts = []
        if graph_facts:
            combined_parts.append("### Knowledge Graph Relational Context:\n" + "\n".join(graph_facts[:8]))

        if vector_context:
            combined_parts.append("### Vector Document Chunks:\n" + vector_context)

        combined_context = "\n\n".join(combined_parts) if combined_parts else ""

        return {
            "query": query,
            "vector_matches": vector_docs,
            "graph_entities": [e.name for e in query_entities],
            "graph_facts": graph_facts,
            "subgraphs": subgraphs,
            "combined_context": combined_context,
        }
