# MultiMind AI — Project Structure

A clean, modular directory layout separates concerns across API routing, agent orchestration, RAG retrieval, multimodal document processing, ML pipelines, business intelligence, database persistence, and automated testing.

```text
multimind-ai/
│
├── app/                                 # Core Python Application Package
│   ├── main.py                          # FastAPI ASGI application & static mounting
│   │
│   ├── api/                             # API Endpoints & Routers
│   │   ├── __init__.py                  # Master router aggregator
│   │   ├── routes_health.py             # Health check & system diagnostics
│   │   ├── routes_auth.py               # User registration & JWT authentication
│   │   ├── routes_documents.py          # Document upload, listing, details & deletion
│   │   ├── routes_chat.py               # Conversational agent chat & session history
│   │   ├── routes_agents.py             # Direct agent endpoints (search, quiz, report, vision)
│   │   └── routes_analysis.py           # ML modeling, BI KPIs, and forecasting routes
│   │
│   ├── agents/                          # Autonomous Multi-Agent System
│   │   ├── __init__.py                  # Package exports
│   │   ├── state.py                     # AgentState & ToolCallRecord dataclasses
│   │   ├── tools.py                     # Verified, safe agent tools (AST calculator, search, etc.)
│   │   ├── orchestrator.py              # Orchestrator, intent routing, coreference resolution
│   │   ├── research_agent.py            # RAG & Knowledge Graph retrieval agent
│   │   ├── document_agent.py            # Summaries & cross-document comparative analysis
│   │   ├── vision_agent.py              # Visual assets, diagram, schematic, and chart analysis
│   │   ├── data_agent.py                # Tabular profiling and CSV/Excel statistical analysis
│   │   ├── quiz_agent.py                # MCQ and assessment question generation
│   │   ├── report_agent.py              # Structured executive intelligence reports
│   │   ├── bi_agent.py                  # Financial KPIs, gross margins, and business insights
│   │   └── forecasting_agent.py         # Time series forecasting and out-of-sample metrics
│   │
│   ├── rag/                             # Retrieval-Augmented Generation Layer
│   │   ├── __init__.py                  # Package exports
│   │   ├── chunking.py                  # Intelligent paragraph/heading-aware chunker
│   │   ├── embeddings.py                # Semantic vector embeddings (384-d deterministic & OpenAI)
│   │   ├── vector_store.py              # Cosine similarity vector engine with persistence
│   │   ├── retriever.py                 # Vector retrieval & context formatter
│   │   ├── reranker.py                  # Hybrid dense + lexical scoring reranker
│   │   ├── prompts.py                   # Strict grounding & citation prompt templates
│   │   └── ingestion.py                 # Multi-step document ingestion pipeline
│   │
│   ├── multimodal/                      # Modality-Specific Parsers
│   │   ├── __init__.py                  # Package exports
│   │   ├── pdf_processor.py             # PyPDF text, page, and heading extractor
│   │   ├── docx_processor.py            # Word document paragraph, style & table extractor
│   │   ├── csv_processor.py             # CSV statistical summarizer & profiler
│   │   ├── excel_processor.py           # Multi-sheet Excel workbook & formula inspector
│   │   └── image_processor.py           # PIL image metadata, luminance, and base64 encoder
│   │
│   ├── graph/                           # GraphRAG & Knowledge Graph
│   │   ├── __init__.py                  # Package exports
│   │   ├── entities.py                  # Concept, Model, Metric & Technology entity extractor
│   │   ├── relationships.py             # Predicate & relationship extractor
│   │   ├── graph_store.py               # NetworkX directed knowledge graph with JSON persistence
│   │   └── graph_retriever.py           # Hybrid Graph + Vector retriever
│   │
│   ├── ml/                              # Machine Learning Module
│   │   ├── __init__.py                  # Package exports
│   │   ├── preprocessing.py             # Imputation, scaling, one-hot encoding, train/test split
│   │   ├── features.py                  # Correlation matrix & multicollinearity analysis
│   │   ├── training.py                  # Classification, regression, clustering, anomaly detection
│   │   ├── evaluation.py                # Metric evaluators (Accuracy, F1, RMSE, Silhouette, etc.)
│   │   └── inference.py                 # Pipeline runner & prediction interface
│   │
│   ├── forecasting/                     # Time Series Forecasting Module
│   │   ├── __init__.py                  # Package exports
│   │   ├── preprocessing.py             # Temporal aggregation, lags & rolling feature engineering
│   │   ├── model.py                     # Autoregressive predictive model wrapper
│   │   ├── training.py                  # Out-of-sample evaluation (MAE, RMSE, MAPE)
│   │   └── inference.py                 # Recursive multi-step forecaster
│   │
│   ├── business_intelligence/           # Commercial & Financial Analytics
│   │   ├── __init__.py                  # Package exports
│   │   ├── kpis.py                      # Revenue, Cost, Profit, Margin, Growth, AOV calculator
│   │   ├── analytics.py                 # Product, Category, and Customer dimension breakdowns
│   │   └── insights.py                  # Strategic insight synthesis
│   │
│   ├── database/                        # Persistence Layer
│   │   ├── __init__.py                  # Package exports
│   │   ├── connection.py                # SQLAlchemy engine, session maker, init_db
│   │   ├── models.py                    # User, Document, Chunk, Conversation, Message, etc.
│   │   └── repositories.py              # Clean CRUD repositories for all entities
│   │
│   ├── services/                        # Business Logic Services
│   │   ├── __init__.py                  # Package exports
│   │   ├── llm_service.py               # Unified LLM provider (Mock offline reasoner, OpenAI, Groq)
│   │   ├── document_service.py          # Document upload, query, summary & deletion
│   │   └── report_service.py            # Markdown report generation & PDF export
│   │
│   ├── config/                          # Configuration Management
│   │   ├── __init__.py                  # Package exports
│   │   └── settings.py                  # Pydantic Settings loaded from .env
│   │
│   └── utils/                           # Shared Utilities
│       ├── __init__.py                  # Package exports
│       ├── logging.py                   # Structured logging with secret masking filter
│       ├── security.py                  # PBKDF2 password hashing, JWT tokens, injection defense
│       └── file_validation.py           # Magic byte validation & filename sanitization
│
├── data/                                # Local Data Directory (git-ignored content)
│   ├── uploads/                         # Stored raw uploaded files
│   ├── processed/                       # Intermediate processed files
│   └── vector_store/                    # Vector index and knowledge graph JSON files
│
├── static/                              # Interactive Web Dashboard UI
│   ├── index.html                       # Single-page application interface
│   ├── style.css                        # Modern dark slate styling & components
│   └── app.js                           # Dashboard client interaction scripts
│
├── tests/                               # Comprehensive Pytest Suite (31 test cases)
│   ├── conftest.py                      # Test fixtures, database, and client setup
│   ├── test_security.py                 # Hashing, tokens, file validation & injection defense
│   ├── test_document_processors.py      # PDF, DOCX, CSV, Excel, Image extraction
│   ├── test_embeddings_vectorstore.py   # Chunking, semantic embeddings & vector store
│   ├── test_rag.py                      # RAG retrieval, citations & fallback tests
│   ├── test_agents.py                   # Orchestrator, intent routing, memory coreference
│   ├── test_ml_bi_forecasting.py        # ML models, BI KPIs, and time series forecasting
│   └── test_graphrag_api.py             # Knowledge Graph and FastAPI REST endpoints
│
├── docs/                                # Technical Documentation
├── .github/workflows/ci.yml             # GitHub Actions CI workflow
├── .env.example                         # Example environment variables
├── .gitignore                           # Git ignore rules
├── requirements.txt                     # Python package dependencies
├── Dockerfile                           # Production Docker container definition
├── docker-compose.yml                   # Multi-container orchestration
└── README.md                            # Comprehensive project overview
```
