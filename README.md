# Bond Credit Due Diligence Agent

A local, evidence-aware financial AI Agent that simulates a junior fixed-income analyst workflow for preliminary bond credit due diligence.

The project runs on synthetic sample data and generates a professional markdown credit report from issuer inputs, financial statements, and source documents. Deterministic Python calculations remain the source of truth. The system does not train a model, does not need labeled data, and does not fabricate financial numbers.

## Role-Fit Positioning

This project is best positioned as an AI algorithm engineering portfolio project for a domain-specific NLP/RAG workflow:

- Python-based AI workflow orchestration for financial credit due diligence.
- Pandas feature engineering from structured financial statements.
- Local NLP retrieval over unstructured documents using TF-IDF with keyword fallback and optional FAISS extension points.
- Explainable rule-based risk detection grounded in calculated financial metrics.
- Evidence-aware report generation with constrained optional LLM polishing.
- Test-covered engineering implementation with clear validation and anti-hallucination boundaries.

For resume and interview packaging, see [`docs/job_alignment_resume_pack.md`](docs/job_alignment_resume_pack.md).

## Motivation

Bond underwriting and credit research require analysts to connect financial statement trends with document evidence: leverage, liquidity, interest coverage, revenue pressure, refinancing risk, and management commentary. This project demonstrates that workflow as an executable agentic pipeline rather than a chatbot.

It is designed to be resume-ready: small enough to explain in interviews, complete enough to demo, and careful about anti-hallucination controls.

## Why This Is Agentic, Not A Chatbot

The system follows a structured workflow with explicit state transitions:

```text
Input documents and financial data
  -> document ingestion and chunking
  -> deterministic financial metric calculator
  -> rule-based credit risk engine
  -> evidence retriever
  -> report generator
  -> human review checklist
```

Each step has a defined responsibility. The agent does not answer free-form questions from memory; it calculates, retrieves evidence, flags risks, and produces a reviewable output.

## Architecture

```text
CLI / Gradio UI
      |
      v
workflow.py
      |
      +--> load_inputs
      +--> parse_documents
      +--> calculate_metrics
      +--> detect_risks
      +--> retrieve_evidence
      +--> generate_report
      +--> human_review_checklist
```

## Modules

- `bond_credit_agent/schemas.py`: Pydantic models for issuer profiles, metrics, risk flags, evidence chunks, workflow state, and reports.
- `bond_credit_agent/financial_metrics.py`: Deterministic financial metric calculations and financial input validation.
- `bond_credit_agent/risk_rules.py`: Rule-based credit risk engine.
- `bond_credit_agent/ingestion.py`: Local document ingestion for `.txt`, `.md`, `.pdf`, `.csv`, and `.xlsx`.
- `bond_credit_agent/chunking.py`: Metadata-preserving chunking with source file and page number support.
- `bond_credit_agent/retriever.py`: Local TF-IDF evidence retrieval with keyword fallback.
- `bond_credit_agent/feature_engineering.py`: Pandas feature frame for credit metrics and transparent risk signal columns.
- `bond_credit_agent/prompt_templates.py`: Constrained prompt templates for fundamentals, debt service, cash flow, liability structure, and operating risk.
- `bond_credit_agent/qa.py`: Local evidence-grounded RAG-style question answering scaffold.
- `bond_credit_agent/report_generator.py`: Deterministic markdown report generation.
- `bond_credit_agent/llm_report.py`: Optional, constrained LLM report polishing with template fallback.
- `bond_credit_agent/workflow.py`: End-to-end orchestration.
- `bond_credit_agent/cli.py`: CLI entrypoint.
- `bond_credit_agent/app.py`: Gradio demo UI.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional ML/RAG extras for experimentation:

```bash
pip install ".[ml]"
```

The core project does not require FAISS, LangChain, PyTorch, Transformers, or XGBoost to run. Those are treated as optional extension points because the sample project intentionally avoids fake model training on synthetic labels.

## CLI Usage

```bash
python -m bond_credit_agent.cli \
  --issuer data/sample/issuer_profile_sample.json \
  --financials data/sample/financials_sample.csv \
  --docs data/sample \
  --output outputs/sample_credit_report.md
```

Optional LLM polishing can be requested, but deterministic template mode remains the default:

```bash
OPENAI_API_KEY=... python -m bond_credit_agent.cli \
  --issuer data/sample/issuer_profile_sample.json \
  --financials data/sample/financials_sample.csv \
  --docs data/sample \
  --output outputs/sample_credit_report.md \
  --use-llm-report
```

If `OPENAI_API_KEY` is missing, the OpenAI SDK is unavailable, or the LLM call fails, the system falls back to the deterministic template report.

## Gradio Usage

```bash
python -m bond_credit_agent.app
```

The UI supports:

- issuer profile JSON upload
- financial CSV or Excel upload
- multiple source document uploads, including `.txt`, `.md`, `.pdf`, `.csv`, and `.xlsx`
- optional LLM report polishing checkbox
- key metrics table
- risk flags table
- evidence table
- markdown credit report
- warnings and human review checklist

UI description: the demo opens with upload controls for issuer, financials, and source documents, followed by a primary `Run Credit Analysis` button and separate panels for metrics, risk flags, retrieved evidence, report text, and review warnings.

## RAG And Evidence Q&A

The retriever indexes local document chunks and returns source-grounded evidence. The implemented path uses Scikit-learn TF-IDF cosine similarity when available, with keyword scoring as a fallback.

The Q&A scaffold is intentionally retrieval-first. It returns evidence snippets and a constrained prompt scaffold rather than inventing an answer. This keeps the system traceable and makes it suitable for future FAISS, LangChain, embedding, or LLM integration.

## Feature Engineering And Model Extension

`feature_engineering.py` exposes calculated financial metrics as a Pandas feature frame and derives deterministic binary risk signal columns. This mirrors the feature layer that a Scikit-learn or XGBoost classifier could consume later, but the repository does not train a classifier because there is no real labeled credit dataset.

This distinction is important in interviews: current risk detection is rule-based and explainable; future ML classification would require audited labels and validation data.

## Sample Data

The sample issuer is fictional: `Northstar Components LLC`, a synthetic industrial electronics manufacturer.

The sample financial CSV includes three years of data and intentionally triggers multiple risk flags:

- high leverage
- weak liquidity
- short-term debt pressure
- weak operating cash flow
- weak interest coverage
- revenue decline
- profitability pressure
- debt expansion pressure

The sample documents are synthetic excerpts styled like a rating report, bond prospectus, annual report excerpt, and covenant note.

## Sample Output

The repository includes:

```text
outputs/sample_credit_report.md
```

The report contains:

- executive summary
- issuer overview
- calculated financial metrics
- risk flag table
- risk flag details
- evidence table with source file, page number, chunk ID, and excerpt
- human review checklist
- preliminary credit opinion
- limitations

## Correctness And Anti-Hallucination Design

- Financial metrics are calculated by Python functions, not generated by an LLM.
- Risk flags are triggered only from calculated metric values.
- Evidence is retrieved from local source documents and attached to each risk flag.
- Risk flags with no evidence are marked as requiring manual analyst review.
- The report explicitly states that it is an AI-generated preliminary analysis requiring human review.
- Optional LLM polishing is off by default and constrained by this prompt requirement:

```text
Use only the provided issuer profile, calculated metrics, risk flags, and evidence. Do not create new facts, ratings, figures, or conclusions.
```

## Tests

```bash
pytest
```

The tests cover deterministic metrics, missing values, zero denominators, feature engineering, risk rules, ingestion metadata, retrieval metadata, evidence Q&A, workflow behavior, report generation, validation errors, LLM fallback without an API key, Gradio helper functions, and CLI execution.

## Limitations

- Synthetic data only; no live issuer database integration.
- No investment recommendation or rating assignment.
- TF-IDF retrieval is useful for a demo but weaker than production semantic retrieval.
- FAISS, LangChain, PyTorch, Transformers, and XGBoost are optional extension points, not required runtime dependencies for the deterministic MVP.
- No supervised risk classifier is trained because synthetic labels would be misleading.
- PDF parsing depends on extractable text quality.
- Optional LLM polishing may improve wording but is not a source of financial truth.
- Human analyst review is required before any real credit decision.

## Future Improvements

- Add real financial database connectors.
- Add SEC/EDGAR or prospectus ingestion pipelines.
- Replace TF-IDF with transformer embeddings, FAISS vector retrieval, and reranking.
- Add LangChain orchestration after the deterministic workflow is stable enough to justify it.
- Train Scikit-learn/XGBoost risk classifiers only with real labeled credit outcomes.
- Improve PDF table extraction and covenant parsing.
- Add multi-issuer comparison and sector-specific risk rules.
- Add structured exports for investment committee memos.
- Add stronger grounding checks for optional LLM-generated prose.

## Resume Bullets

- Built a structured bond credit due diligence Agent in Python, orchestrating document ingestion, financial metric calculation, rule-based risk detection, RAG-style evidence retrieval, and human-in-the-loop report generation.
- Implemented Pandas-based financial feature engineering and deterministic risk signal detection for leverage, liquidity, cash flow, interest coverage, revenue decline, profitability pressure, and debt growth.
- Developed a metadata-preserving local retrieval layer with TF-IDF, optional FAISS indexing, and constrained prompt templates for issuer fundamentals, debt service capacity, cash flow quality, liability structure, and operating risk.
- Delivered an interactive Gradio demo with document upload, sample-analysis mode, evidence Q&A, risk visualizations, markdown report generation, and pytest-backed validation.

## Interview Talking Points

- The project does not need labeled training data because it is not a supervised learning task. The core work is deterministic financial analysis plus evidence retrieval.
- Hallucination is controlled by making Python calculations the source of truth and requiring every risk flag to originate from calculated metrics.
- The deterministic parts are financial metric calculation, risk threshold evaluation, evidence attachment rules, and template report generation.
- RAG is used to support analyst review: retrieved chunks provide document context, but they do not override calculated metrics.
- The project includes a feature engineering layer compatible with future Scikit-learn/XGBoost experiments, but it does not train on fabricated labels.
- FAISS/LangChain/PyTorch/Transformers are best framed as optional next-step integrations unless a real corpus and evaluation setup are available.
- The workflow resembles bond underwriting and credit research because it connects issuer profile, financial statements, source documents, risk flags, and analyst review questions.
- A production version could connect to real financial databases, improve document parsing, use vector retrieval with reranking, and add stricter LLM grounding checks.
