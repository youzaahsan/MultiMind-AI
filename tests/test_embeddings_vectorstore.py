import pytest
from app.rag.chunking import IntelligentChunker
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore

def test_intelligent_chunking_paragraphs():
    chunker = IntelligentChunker(chunk_size=20, chunk_overlap=5)
    extracted = {
        "full_text": "This is paragraph one containing multiple words to verify chunk boundary preservation.\n\nThis is paragraph two providing distinct conceptual content."
    }
    chunks = chunker.chunk_document("doc-1", "test.txt", extracted)
    assert len(chunks) >= 2
    assert chunks[0]["document_id"] == "doc-1"
    assert chunks[0]["filename"] == "test.txt"
    assert "page_number" in chunks[0]
    assert "metadata" in chunks[0]

def test_embeddings_similarity():
    service = EmbeddingService(dim=64)
    v1 = service.embed_text("neural network deep learning model")
    v2 = service.embed_text("neural network deep learning architecture")
    v3 = service.embed_text("baking strawberry cheesecake in kitchen")

    # Cosine similarity
    import numpy as np
    sim_1_2 = np.dot(v1, v2)
    sim_1_3 = np.dot(v1, v3)

    assert sim_1_2 > sim_1_3
    assert sim_1_2 > 0.5

def test_vector_store_crud(tmp_path):
    store = VectorStore(storage_dir=str(tmp_path))
    texts = [
        "Supervised learning requires labeled ground truth training examples.",
        "Unsupervised learning finds hidden groupings without target outcomes.",
    ]
    emb_service = EmbeddingService(dim=64)
    embeddings = emb_service.embed_batch(texts)
    metadatas = [
        {"document_id": "doc_a", "page": 1, "filename": "sl.pdf"},
        {"document_id": "doc_b", "page": 2, "filename": "ul.pdf"},
    ]

    ids = store.add_texts(texts=texts, embeddings=embeddings, metadatas=metadatas)
    assert len(ids) == 2
    assert store.count() == 2

    # Similarity search
    q_emb = emb_service.embed_text("What requires labeled training examples?")
    results = store.similarity_search(query_embedding=q_emb, top_k=1)
    assert len(results) == 1
    assert "Supervised learning" in results[0]["content"]
    assert results[0]["metadata"]["filename"] == "sl.pdf"

    # Delete by document id
    deleted = store.delete_by_document_id("doc_a")
    assert deleted == 1
    assert store.count() == 1
