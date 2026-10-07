# MultiMind AI — Setup & Installation Guide

This guide walks through setting up MultiMind AI on your local machine for development, testing, and production experimentation.

---

## 1. Prerequisites

* **Operating System:** Windows, macOS, or Linux.
* **Python Version:** Python 3.11, 3.12, 3.13, or 3.14.
* **Git:** Version control installed.
* **Memory:** Minimum 4GB RAM (8GB+ recommended).

---

## 2. Local Environment Setup

### Step 1: Clone or Navigate to the Repository
```bash
cd "working-directory/multimind-ai"
```

### Step 2: Create and Activate Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux / macOS (Bash):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Environment Configuration

Copy the sample environment file:
```bash
# On Linux/macOS
cp .env.example .env

# On Windows (PowerShell)
Copy-Item .env.example .env
```

### Key Configuration Variables:
| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `development` | Environment mode (`development`, `production`, `test`) |
| `APP_PORT` | `8000` | HTTP port for FastAPI and Dashboard |
| `DATABASE_URL` | `sqlite:///./data/multimind.db` | Database URL (SQLite or PostgreSQL) |
| `LLM_PROVIDER` | `mock` | LLM backend: `mock` (offline local reasoning), `openai`, `groq` |
| `LLM_API_KEY` | `""` | Optional API key when using OpenAI or cloud LLMs |
| `EMBEDDING_PROVIDER` | `mock` | `mock` (384-d deterministic semantic projection) or `openai` |
| `VECTOR_DB_PATH` | `./data/vector_store` | Path for saving vector indices and graph JSON |
| `MAX_UPLOAD_SIZE_MB`| `50` | Maximum allowed uploaded file size in MB |

> **Note on Zero External Dependencies:** MultiMind AI runs completely out of the box with zero external API keys required! Setting `LLM_PROVIDER=mock` and `EMBEDDING_PROVIDER=mock` enables the internal deterministic reasoning and semantic vector projection engine, making it runnable immediately offline.

---

## 4. Initializing Database and Vector Store

MultiMind AI automatically creates SQLite database tables, uploads directory, and vector store indices on application startup:
```bash
python -c "from app.main import app; print('Environment verified successfully!')"
```

---

## 5. Running the Application

Start the FastAPI application with Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Once started:
* **Interactive Web Dashboard:** Open [http://localhost:8000](http://localhost:8000) in your browser.
* **Interactive API Documentation (Swagger UI):** Open [http://localhost:8000/docs](http://localhost:8000/docs).
* **ReDoc Documentation:** Open [http://localhost:8000/redoc](http://localhost:8000/redoc).
* **Health Check Endpoint:** Open [http://localhost:8000/health](http://localhost:8000/health).

---

## 6. Running Tests

To verify all system modules:
```bash
pytest tests -v
```
All 31 test suites across ingestion, chunking, embeddings, RAG, agents, ML, forecasting, BI, and APIs should pass.
