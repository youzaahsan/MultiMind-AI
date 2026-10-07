# MultiMind AI — Autonomous Agents & Tools Reference

MultiMind AI deploys an Orchestrator and eight specialized cognitive agents. Each agent possesses bounded capabilities, strict tool interfaces, and verified output schemas.

---

## 1. Agent Inventory

| Agent Name | Primary Responsibility | Primary Tools Used |
| :--- | :--- | :--- |
| **Orchestrator Agent** | Intent classification, coreference resolution, agent routing | Safe Calculator, Tool Registry |
| **Research Agent** | Domain knowledge QA, dense retrieval, citation grounding | `document_search`, `semantic_search` |
| **Document Agent** | Executive document summaries, cross-document comparison | `summarize_document`, `document_search` |
| **Vision Agent** | Interpreting diagrams, charts, schematics, and screenshots | `analyze_image` |
| **Data Analysis Agent** | Tabular profiling, CSV/Excel metrics, missing values | `analyze_csv`, `analyze_excel` |
| **Quiz Agent** | MCQ knowledge assessment and answer key generation | `generate_quiz`, `document_search` |
| **Report Agent** | Multi-section structured executive intelligence reports | `generate_report`, `document_search` |
| **BI Agent** | Revenue, Cost, Profit, Profit Margins, Growth Rates | `business_analysis` |
| **Forecasting Agent**| Autoregressive predictive modeling and validation | `forecasting` |

---

## 2. Agent Tool Implementations (`app/agents/tools.py`)

All tools execute actual computational logic with zero arbitrary code execution:

1. **`document_search(query: str, top_k: int = 4)`**
   * Preprocesses query, embeds into 384-d vector, performs cosine similarity search, reranks candidates, and extracts citations.
2. **`summarize_document(text_or_context: str)`**
   * Synthesizes hierarchical summary highlighting core methodology, components, and conclusions.
3. **`analyze_image(image_path: str, prompt: str)`**
   * Loads image via Pillow, extracts dimensions, aspect ratio, luminance, and passes base64 encoding to Vision reasoning model.
4. **`analyze_csv(file_path: str)`**
   * Reads dataset using pandas, calculates descriptive statistics for numeric columns, categorical frequencies, and missing value rates.
5. **`analyze_excel(file_path: str)`**
   * Uses openpyxl and pandas to inspect sheet names, sheet dimensions, formula coordinates, and sheet-by-sheet statistics.
6. **`calculator(expression: str)`**
   * Parses arithmetic expressions into an Abstract Syntax Tree (AST), executing ONLY verified safe operators (`+`, `-`, `*`, `/`, `^`, `%`).
7. **`generate_quiz(topic_or_context: str, num_questions: int = 5)`**
   * Creates grounded 4-option multiple choice questions with explicit explanations and correct answer keys.
8. **`generate_report(topic: str, context: str)`**
   * Formats a formal 5-section briefing: Executive Summary, Objectives, Findings, Strategic Risks, and Actionable Recommendations.
9. **`business_analysis(df: pd.DataFrame)`**
   * Computes Revenue, Cost, Gross Profit, Gross Margin %, Average Order Value, and Pareto dimensions.
10. **`forecasting(df: pd.DataFrame, date_col: str, target_col: str, horizon: int)`**
    * Generates calendar and autoregressive lag features, trains model, evaluates MAE/RMSE/MAPE on holdout window, and outputs recursive projections.
