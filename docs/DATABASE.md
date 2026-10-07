# MultiMind AI — Database Architecture & Schema

MultiMind AI uses **SQLAlchemy 2.0+ ORM** supporting SQLite (default, zero-configuration local run) and PostgreSQL (production).

---

## 1. Entity-Relationship Diagram

```mermaid
erDiagram
    User ||--o{ Conversation : owns
    Conversation ||--o{ Message : contains
    Document ||--o{ DocumentChunk : contains
    
    User {
        string id PK
        string email
        string hashed_password
        string full_name
        boolean is_active
        boolean is_admin
        datetime created_at
    }

    Document {
        string id PK
        string filename
        string file_path
        string file_type
        int file_size_bytes
        int total_pages
        int chunk_count
        string status
        json metadata_info
        text summary
        datetime created_at
    }

    DocumentChunk {
        string id PK
        string document_id FK
        int chunk_index
        text content
        int page_number
        string section
        string modality
        int token_count
        json metadata_info
        datetime created_at
    }

    Conversation {
        string id PK
        string session_id
        string user_id FK
        string title
        datetime created_at
        datetime updated_at
    }

    Message {
        string id PK
        string conversation_id FK
        string role
        text content
        json sources
        string agent_name
        string model
        int tokens_used
        datetime created_at
    }

    AgentSession {
        string id PK
        string session_id
        string agent_name
        string status
        json plan
        json execution_trace
        datetime created_at
    }

    Report {
        string id PK
        string title
        string topic
        text summary
        text content
        json sources
        string format
        datetime created_at
    }

    AnalysisResult {
        string id PK
        string filename
        string analysis_type
        text summary
        json raw_results
        json insights
        datetime created_at
    }

    ForecastResult {
        string id PK
        string filename
        string date_column
        string target_column
        string model_name
        int horizon_periods
        json metrics
        json historical_points
        json forecast_points
        datetime created_at
    }
```

---

## 2. Table Specifications & Indexes

### 2.1 `documents` & `document_chunks`
* **Cascade Deletion:** When a document is deleted, all associated `document_chunks` are automatically removed via `ondelete="CASCADE"`.
* **Index `idx_doc_chunk_order`:** Composite index on `(document_id, chunk_index)` accelerates ordered reconstruction of document sections.
* **Fields:** `modality` tracks whether chunk originated from plain text, table markdown, or OCR image descriptions.

### 2.2 `conversations` & `messages`
* **Session ID Index:** `session_id` is indexed for fast conversational memory retrieval.
* **Sources JSON:** Stores grounded citation references `[{"filename": "...", "page": 1, "section": "..."}]`.

### 2.3 `analysis_results` & `forecast_results`
* Stores validated mathematical metrics (Accuracy, F1, MAE, RMSE, MAPE) and historical/projected points for rendering graphs on the dashboard.

---

## 3. Database Migration & Switching to PostgreSQL

To switch to PostgreSQL in production:
1. Update `DATABASE_URL` in `.env`:
   ```bash
   DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/multimind_db
   ```
2. MultiMind AI uses `psycopg-binary` which is included in `requirements.txt`.
3. Startup lifecycle calls `init_db()` which automatically creates all tables.
