import pytest
from app.graph.entities import EntityExtractor
from app.graph.relationships import RelationshipExtractor
from app.graph.graph_store import KnowledgeGraphStore
from app.graph.graph_retriever import GraphRAGRetriever

def test_graph_extraction_and_store(tmp_path):
    text = "LangGraph implements agent workflows. FastAPI uses Pydantic for validation."
    e_extractor = EntityExtractor()
    r_extractor = RelationshipExtractor()

    entities = e_extractor.extract(text)
    assert len(entities) >= 2
    e_names = [e.name.lower() for e in entities]
    assert "fastapi" in e_names or "langgraph" in e_names

    relationships = r_extractor.extract(text, entities)
    assert len(relationships) >= 1

    store = KnowledgeGraphStore(persistence_path=str(tmp_path))
    store.add_extracted_knowledge(entities, relationships)
    summary = store.get_summary()
    assert summary["total_nodes"] >= 2
    assert summary["total_edges"] >= 1

def test_api_health_endpoint(test_client):
    res = test_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "components" in data

def test_api_auth_and_chat(test_client):
    # 1. Register
    reg_res = test_client.post("/auth/register", json={
        "email": "researcher@multimind.ai",
        "password": "Password123!",
        "full_name": "AI Researcher",
    })
    assert reg_res.status_code == 201
    assert "access_token" in reg_res.json()

    # 2. Chat with agent
    chat_res = test_client.post("/chat", json={
        "message": "What is 25 * 40?",
    })
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "1000" in chat_data["response"] or chat_data["active_agent"] == "calculator"

    # 3. Check conversation history
    conv_res = test_client.get(f"/conversation/{chat_data['session_id']}")
    assert conv_res.status_code == 200
    assert conv_res.json()["message_count"] >= 2

def test_api_upload_and_documents(test_client):
    file_content = b"Multimodal intelligence platform testing document."
    upload_res = test_client.post(
        "/upload",
        files={"file": ("test_doc.txt", file_content, "text/plain")},
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    doc_id = doc_data["document_id"]

    # List documents
    list_res = test_client.get("/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert any(d["id"] == doc_id for d in docs)

    # Delete document
    del_res = test_client.delete(f"/documents/{doc_id}")
    assert del_res.status_code == 200
