# MultiMind AI — REST API Documentation

Base URL: `http://localhost:8000` (or `http://localhost:8000/api`)

All endpoints support JSON request/response formats except `/upload` which uses `multipart/form-data`.

---

## 1. System & Health

### `GET /health`
Returns system health, database status, indexed vector count, and knowledge graph summary.
* **Status:** `200 OK`
* **Response Example:**
```json
{
  "status": "healthy",
  "app_name": "MultiMind AI",
  "environment": "development",
  "version": "1.0.0",
  "timestamp": "2026-10-06T00:15:00Z",
  "components": {
    "database": "healthy",
    "vector_store_documents_indexed": 42,
    "knowledge_graph_summary": {
      "total_nodes": 18,
      "total_edges": 24,
      "density": 0.0784
    },
    "llm_provider": "mock",
    "embedding_provider": "mock"
  }
}
```

---

## 2. Authentication

### `POST /auth/register`
Creates a new user account.
* **Status:** `201 Created`
* **Request:**
```json
{
  "email": "user@multimind.ai",
  "password": "StrongPassword123!",
  "full_name": "Ada Lovelace"
}
```
* **Response:**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "email": "user@multimind.ai"
}
```

### `POST /auth/login`
Authenticates a user and issues a signed JWT token.
* **Status:** `200 OK`
* **Request:**
```json
{
  "email": "user@multimind.ai",
  "password": "StrongPassword123!"
}
```

---

## 3. Documents & Ingestion

### `POST /upload`
Uploads and processes any supported document (`.pdf`, `.docx`, `.txt`, `.csv`, `.xlsx`, `.png`, `.jpg`, `.webp`).
* **Status:** `201 Created`
* **Request:** Multipart form with field `file`.
* **Response Example:**
```json
{
  "document_id": "a3b98c76-2f10-410a-85e8-5b12da6899e4",
  "filename": "neural_networks.pdf",
  "file_type": ".pdf",
  "file_size": 245100,
  "total_pages": 12,
  "chunks_count": 28,
  "summary": "PDF document 'neural_networks.pdf' with 12 page(s) and approximately 6500 words.",
  "status": "processed"
}
```

### `GET /documents`
Lists all ingested documents.
* **Query Parameters:** `limit` (default: 100), `offset` (default: 0).
* **Status:** `200 OK`

### `GET /documents/{id}`
Returns metadata, statistics, and summary for a single document.
* **Status:** `200 OK` (or `404 Not Found`)

### `DELETE /documents/{id}`
Removes a document from disk, relational database, and vector index.
* **Status:** `200 OK`

### `POST /summarize`
Summarizes an existing document ID or raw text payload.
* **Request:**
```json
{
  "document_id": "a3b98c76-2f10-410a-85e8-5b12da6899e4"
}
```

---

## 4. Chat & Autonomous Agents

### `POST /chat`
Core multi-agent conversational endpoint.
* **Status:** `200 OK`
* **Request:**
```json
{
  "message": "What does this document say about supervised learning?",
  "session_id": "optional-session-id"
}
```
* **Response Example:**
```json
{
  "session_id": "session_abc123",
  "response": "Supervised learning utilizes labeled training datasets...\n\nSources:\n- machine_learning.pdf — Page 7",
  "sources": [
    {
      "filename": "machine_learning.pdf",
      "page": 7,
      "section": "Fundamentals"
    }
  ],
  "active_agent": "research_agent",
  "routing_reason": "Query involves general information retrieval and document QA.",
  "tool_calls": [
    {
      "tool_name": "document_search",
      "arguments": {"query": "What does this document say about supervised learning?", "top_k": 4},
      "output": {"matches": 3}
    }
  ]
}
```

### `GET /conversation/{session_id}`
Retrieves chronological message history for a conversation.
* **Status:** `200 OK`

---

## 5. Direct Agent Capabilities

### `POST /search`
Semantic search across documents with optional GraphRAG entity retrieval.
* **Request:**
```json
{
  "query": "Deep learning architectures and transformer models",
  "top_k": 4,
  "use_graph": true
}
```

### `POST /generate-quiz`
Generates multiple choice questions and answer keys.
* **Request:**
```json
{
  "topic_or_context": "Convolutional Neural Networks and pooling layers",
  "num_questions": 5
}
```

### `POST /generate-report`
Generates a formal, structured intelligence report.
* **Request:**
```json
{
  "topic": "Enterprise Multimodal RAG Implementations",
  "context": "Focus on production architectures, security, and latency tradeoffs."
}
```

### `POST /analyze-image`
Analyzes technical diagrams, charts, or UI screenshots.
* **Request:**
```json
{
  "image_path": "data/uploads/system_diagram.png",
  "prompt": "Explain the architectural components and dataflow."
}
```

---

## 6. Data Analysis, ML & Forecasting

### `POST /analyze-data`
Executes complete scikit-learn machine learning pipelines.
* **Request:**
```json
{
  "file_path": "data/uploads/customer_data.csv",
  "task_type": "classification",
  "target_column": "churn"
}
```

### `POST /analytics`
Computes financial and commercial KPIs (Revenue, Cost, Profit, Margin, Growth).
* **Request:**
```json
{
  "file_path": "data/uploads/sales.csv",
  "revenue_column": "revenue",
  "cost_column": "cost",
  "dimension_column": "product"
}
```

### `POST /forecast`
Executes autoregressive time series demand/sales forecasting.
* **Request:**
```json
{
  "file_path": "data/uploads/daily_sales.csv",
  "date_column": "date",
  "target_column": "sales",
  "horizon_periods": 7
}
```
