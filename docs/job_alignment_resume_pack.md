# AI Algorithm Engineer Resume Pack

This document packages the project for an AI algorithm development engineer role while keeping the project scope accurate. The current implementation is an explainable AI workflow with NLP retrieval and deterministic financial feature engineering. It does not claim to train a deep learning model on fabricated labels.

## One-Sentence Project Pitch

Built a Python-based bond credit due diligence AI agent that combines financial feature engineering, rule-based risk detection, local NLP evidence retrieval, constrained LLM report polishing, and human-review controls to generate traceable preliminary credit risk reports.

## JD Alignment

| Job Requirement | Project Evidence |
| --- | --- |
| AI algorithm and model development | Implements an end-to-end AI workflow for domain-specific risk analysis; separates feature calculation, risk detection, retrieval, and report generation into modular components. |
| Machine learning / deep learning / NLP awareness | Uses NLP retrieval over local documents through TF-IDF, keyword fallback, prompt templates, and optional FAISS / LangChain / Transformer extension points. |
| Data preprocessing and feature engineering | Parses CSV/XLSX financial statements, validates required fields, converts numeric inputs, and exposes calculated credit metrics as a Pandas feature frame. |
| Model performance and explainability | Uses transparent thresholds for leverage, liquidity, cash flow, interest coverage, revenue decline, profitability, and debt growth; every risk flag records metric values and reasoning. |
| Software engineering ability | Provides CLI, Gradio demo helpers, Pydantic schemas, modular package structure, input validation, fallback behavior, and pytest coverage. |
| Data processing tools such as SQL/Pandas | Uses Pandas for financial data loading, cleaning, metric calculation, and tabular feature generation. |
| AI model integration into real applications | Integrates retrieval, optional LLM polishing, report generation, and human review checklist into a usable workflow. |
| Communication and business understanding | Maps technical outputs to credit analyst workflows: risk flags, evidence excerpts, recommendations, limitations, and manual review checklist. |

## Resume Bullets

Use 2 to 4 bullets depending on space:

- Built a Python-based bond credit due diligence AI agent, orchestrating document ingestion, financial feature engineering, rule-based risk detection, NLP evidence retrieval, and human-in-the-loop report generation.
- Implemented deterministic credit metric calculators with Pandas for leverage, liquidity, cash flow, interest coverage, revenue growth, profitability, and debt expansion signals, with validation for missing values and zero denominators.
- Developed a local RAG-style retrieval layer using TF-IDF with keyword fallback and metadata-preserving chunks, linking each triggered risk flag to source-file evidence and manual-review status.
- Designed constrained prompt templates and optional LLM report polishing that preserve calculated metrics, prevent fabricated financial facts, and fall back to deterministic Markdown generation when unavailable.
- Added pytest coverage across metric logic, risk rules, ingestion, retrieval, Q&A scaffolding, workflow orchestration, validation errors, report generation, and UI helper functions.

## Short Chinese Resume Version

债券信用尽调 AI Agent：基于 Python 构建面向固定收益信用分析的本地 AI 工作流，整合财务报表解析、Pandas 特征工程、规则化风险识别、TF-IDF/RAG 式证据检索和可复核报告生成；实现杠杆率、流动性、现金流、利息覆盖倍数、收入增长、盈利能力和债务增长等核心信用指标的确定性计算，并为每个风险旗标绑定来源文档证据、解释逻辑和人工复核清单，使用 pytest 覆盖指标计算、风险规则、检索、报告和端到端流程。

## Interview Explanation

### 1. What problem does it solve?

Bond credit analysis requires analysts to connect structured financial statement data with unstructured evidence from prospectuses, rating reports, annual report excerpts, and covenant notes. This project automates the first-pass workflow: calculate metrics, flag risks, retrieve supporting evidence, and generate a transparent preliminary report.

### 2. Why is it an AI project rather than a simple script?

It is not a free-form chatbot. It is an agentic workflow with explicit state transitions:

```text
Inputs
  -> data validation
  -> document parsing and chunking
  -> financial feature calculation
  -> risk rule engine
  -> evidence retrieval
  -> report generation
  -> human review checklist
```

The AI part is concentrated in retrieval-augmented evidence handling, prompt scaffolding, optional LLM polishing, and workflow orchestration. The financial numbers remain deterministic.

### 3. How does the NLP/RAG part work?

Local source documents are parsed into metadata-preserving chunks. The retriever indexes chunk text and ranks evidence by similarity to each risk flag's query. When Scikit-learn is available, it uses TF-IDF cosine similarity; otherwise it falls back to keyword scoring. The Q&A scaffold returns evidence snippets and a constrained prompt rather than inventing an answer.

### 4. How is hallucination controlled?

The project uses three controls:

- Financial metrics are calculated only by Python functions.
- Risk flags are triggered only from calculated metric values.
- Reports and optional LLM prompts explicitly forbid adding facts, ratings, figures, or conclusions not present in the inputs.

If no supporting evidence is retrieved, the risk remains marked for manual review.

### 5. Where is feature engineering?

`bond_credit_agent/feature_engineering.py` converts calculated financial metrics into a one-row Pandas feature frame and creates deterministic binary signal columns. This mirrors the feature layer that could later feed a supervised model, while avoiding fake model training on synthetic labels.

### 6. Why not train a deep learning model?

Because the sample data is synthetic and does not contain audited real credit outcomes. Training a classifier on fabricated labels would be misleading. The current design is honest and production-oriented: deterministic rules now, supervised ML later only when real labeled credit data and validation sets exist.

## Safe Way To Discuss Future ML Extensions

You can say:

> The current MVP is explainable and rule-based because financial correctness is more important than pretending to have a model. If real labeled issuer outcomes were available, I would reuse the existing feature frame, add time-aware train/test splits, compare logistic regression, XGBoost, and calibrated tree models, evaluate precision/recall for risk flags, and keep SHAP or feature-attribution reports for explainability.

Avoid saying:

- "I trained a deep learning credit model" unless you actually add that with real data.
- "The model predicts default probability" because the current project does not have default labels.
- "The LLM performs credit analysis" because the LLM is optional and not the source of truth.

## Two-Minute Interview Script

This project is a bond credit due diligence AI agent. The goal is to simulate a junior fixed-income analyst's first-pass workflow: read issuer data, calculate financial metrics, flag credit risks, retrieve supporting evidence, and produce a human-reviewable report.

The architecture is modular. `financial_metrics.py` calculates leverage, liquidity, cash flow, interest coverage, growth, margin, and debt expansion metrics using Pandas. `risk_rules.py` maps those calculated metrics to transparent risk flags. `ingestion.py` and `chunking.py` parse local source documents and preserve metadata such as source file and page number. `retriever.py` performs local NLP retrieval with TF-IDF and fallback keyword scoring, so every risk can be linked back to supporting evidence.

The main design principle is anti-hallucination. The LLM is optional and only used for report polishing. It cannot invent numbers or conclusions. If evidence is missing, the report marks the item for manual review. This makes the project explainable and suitable for financial workflows where correctness and auditability matter.

From an AI engineering perspective, the project demonstrates data preprocessing, feature engineering, retrieval-augmented generation scaffolding, prompt constraints, modular Python engineering, and test coverage. A production extension would add real issuer data, vector retrieval with reranking, and supervised risk models only after real labeled credit outcomes are available.

## Technical Stack To List

Python, Pandas, Pydantic, Scikit-learn TF-IDF, local RAG, prompt engineering, optional OpenAI API, optional FAISS / LangChain / Transformers extension points, Gradio, pytest.

## Suggested Project Title

Use one of these:

- Bond Credit Due Diligence AI Agent
- Evidence-Grounded Credit Risk Analysis Agent
- Local RAG Workflow for Bond Credit Risk Review

## GitHub README Summary

Use this as the top-of-repo summary if needed:

> A local, evidence-grounded AI workflow for preliminary bond credit due diligence. The system parses issuer profiles, financial statements, and source documents; calculates credit metrics with deterministic Python functions; applies explainable risk rules; retrieves supporting evidence with local NLP retrieval; and generates a transparent Markdown report with human-review controls.
