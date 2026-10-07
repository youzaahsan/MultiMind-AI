import pytest
from app.rag.retriever import RAGRetriever
from app.rag.reranker import Reranker
from app.rag.vector_store import VectorStore
from app.rag.embeddings import EmbeddingService
from app.services.llm_service import LLMService

def test_rag_retrieval_and_reranking(tmp_path):
    store = VectorStore(storage_dir=str(tmp_path))
    service = EmbeddingService(dim=64)
    texts = [
        "Convolutional neural networks specialize in image feature extraction and spatial grids.",
        "Gradient descent minimizes the objective loss function across iterations.",
    ]
    metas = [
        {"document_id": "doc1", "filename": "cnn.pdf", "page": 12, "section": "Vision", "modality": "text"},
        {"document_id": "doc2", "filename": "optimization.pdf", "page": 5, "section": "Math", "modality": "text"},
    ]
    store.add_texts(texts=texts, embeddings=service.embed_batch(texts), metadatas=metas)

    retriever = RAGRetriever(vector_store=store, embedding_service=service, reranker=Reranker())
    matches, context = retriever.retrieve("spatial grids and convolutional networks", top_k=1)

    assert len(matches) == 1
    assert "cnn.pdf" in context
    assert "Page: 12" in context

def test_rag_grounded_answer_and_citation():
    llm = LLMService(provider="mock")
    prompt = (
        "Document Context:\n---------------------\n"
        "[Source 1: ml_guide.pdf | Page: 7 | Section: Fundamentals | Modality: text]\n"
        "Supervised learning trains a model on input features mapped to verified ground truth targets.\n"
        "---------------------\n\n"
        "User Question:\nWhat does supervised learning do?"
    )
    ans = llm.generate(prompt=prompt)
    assert "Supervised learning trains a model" in ans
    assert "Sources:" in ans
    assert "ml_guide.pdf — Page 7" in ans

def test_rag_missing_context_fallback():
    llm = LLMService(provider="mock")
    prompt = (
        "Document Context:\n---------------------\n"
        "[Source 1: recipe.pdf | Page: 1 | Section: Kitchen | Modality: text]\n"
        "Add two cups of flour and stir gently until smooth.\n"
        "---------------------\n\n"
        "User Question:\nHow do quantum neural networks calculate gradient tensors?"
    )
    ans = llm.generate(prompt=prompt)
    assert ans == "I could not find this information in the uploaded documents."
