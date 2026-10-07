# MultiMind AI — Development Guide

This guide covers coding standards, branching models, dependency management, error handling, and extending agents and multimodal processors.

---

## 1. Development Principles

1. **Strict Type Hinting:** All functions and methods must use complete type annotations (`typing.List`, `Dict`, `Optional`, `Tuple`, etc.).
2. **Defensive Error Handling:** Never allow unhandled exceptions or silent failures. Wrap I/O and external calls with logging.
3. **No Dynamic Execution:** Under no circumstances should `eval()` or `exec()` be used. Use Python's `ast` for mathematical parsing.
4. **Zero Fabrication:** Never invent machine learning metrics or hallucinate citations. Grounded responses must reference actual document chunks.

---

## 2. Adding a New Document Modality

To add support for a new file type (e.g. Markdown, EPUB):

1. **Create Processor in `app/multimodal/`:**
   ```python
   # app/multimodal/markdown_processor.py
   class MarkdownProcessor:
       def __init__(self, file_path: Path):
           self.file_path = file_path
       def extract(self) -> Dict[str, Any]:
           # Extract headings, code blocks, tables, and text
           ...
   ```
2. **Register in `app/rag/ingestion.py`:**
   Add extension check in `_extract_content`:
   ```python
   elif ext in [".md", ".markdown"]:
       processor = MarkdownProcessor(saved_path)
       data = processor.extract()
       return data, "text", 1
   ```
3. **Add File Extension to Settings:**
   Ensure `ALLOWED_EXTENSIONS` includes the new suffix in `.env`.
4. **Write Unit Tests in `tests/test_document_processors.py`:**
   Assert content extraction, page count, and structure.

---

## 3. Adding a New Specialized Agent

To add a new agent (e.g., `CodeAuditAgent`):

1. **Define Agent in `app/agents/code_audit_agent.py`:**
   ```python
   class CodeAuditAgent:
       def __init__(self, tools: ToolRegistry, llm: LLMService):
           self.tools = tools
           self.llm = llm

       def run(self, state: AgentState) -> AgentState:
           # Execute tools and update state
           return state
   ```
2. **Register in `app/agents/orchestrator.py`:**
   * Instantiate inside `OrchestratorAgent.__init__`.
   * Add intent classification logic in `_classify_intent()`.
   * Add delegation branch in `route_and_execute()`.
3. **Register New Tools in `app/agents/tools.py`:**
   Ensure each tool has strict inputs and safe execution.
4. **Add Pytest Cases in `tests/test_agents.py`:**
   Verify routing triggers on relevant queries and records tool calls.

---

## 4. Code Quality & Linting

Run tests and check linting:
```bash
# Run pytest with timing
pytest -v --durations=10

# Verify settings and models import cleanly
python -c "from app.main import app; print('All modules loaded.')"
```
