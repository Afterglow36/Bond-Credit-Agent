from __future__ import annotations

import tempfile
import argparse
import socket
from pathlib import Path
from typing import Any

import pandas as pd

from bond_credit_agent.exceptions import UserInputError
from bond_credit_agent.qa import retrieve_question_evidence
from bond_credit_agent.schemas import CreditReport
from bond_credit_agent.workflow import run_workflow

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ISSUER = PROJECT_ROOT / "data" / "sample" / "issuer_profile_sample.json"
SAMPLE_FINANCIALS = PROJECT_ROOT / "data" / "sample" / "financials_sample.csv"
SAMPLE_DOCS = PROJECT_ROOT / "data" / "sample"

EMPTY_TABLE = pd.DataFrame()

APP_CSS = """
.gradio-container {
    max-width: 1440px !important;
}
.app-header {
    border-bottom: 1px solid #e5e7eb;
    padding: 12px 0 18px 0;
    margin-bottom: 8px;
}
.app-header h1 {
    font-size: 30px;
    line-height: 1.2;
    margin-bottom: 6px;
}
.app-header p {
    color: #4b5563;
    margin: 0;
}
.summary-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin: 8px 0 12px;
}
.summary-card {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 14px;
    background: #ffffff;
}
.summary-label {
    color: #6b7280;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: .04em;
}
.summary-value {
    font-size: 26px;
    font-weight: 700;
    margin-top: 4px;
}
.summary-card:first-child .summary-value {
    font-size: 22px;
    line-height: 1.25;
    overflow-wrap: anywhere;
}
.summary-note {
    color: #4b5563;
    font-size: 13px;
    margin-top: 4px;
}
.status-strip {
    border-left: 4px solid #334155;
    background: #f8fafc;
    padding: 12px 14px;
    border-radius: 6px;
    margin: 10px 0;
}
"""


def metrics_table(report) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "metric": metric.name,
                "year": metric.year,
                "value": metric.value,
                "note": metric.explanation,
            }
            for metric in report.metrics.values()
        ]
    )


def risk_flags_table(report) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for flag in report.risk_flags:
        rows.append(
            {
                "risk_type": flag.risk_type,
                "severity": flag.severity,
                "metric_values": ", ".join(f"{name}={value:.4f}" if value is not None else f"{name}=N/A" for name, value in flag.related_metric_values.items()),
                "evidence_summary": flag.evidence_summary,
                "manual_review_required": flag.manual_review_required,
            }
        )
    return pd.DataFrame(rows)


def evidence_table(report) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for flag in report.risk_flags:
        for chunk in flag.evidence:
            rows.append(
                {
                    "risk_type": flag.risk_type,
                    "source_file": chunk.source_file,
                    "page_number": chunk.page_number,
                    "chunk_id": chunk.chunk_id,
                    "score": round(chunk.score, 4),
                    "snippet": chunk.text[:500],
                }
            )
    return pd.DataFrame(rows)


def qa_evidence_table(chunks) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source_file": chunk.source_file,
                "page_number": chunk.page_number,
                "chunk_id": chunk.chunk_id,
                "score": round(chunk.score, 4),
                "snippet": chunk.text[:500],
            }
            for chunk in chunks
        ]
    )


def warnings_and_checklist(report) -> str:
    lines: list[str] = []
    if report.ingestion_warnings:
        lines.append("Document ingestion warnings:")
        lines.extend(f"- {warning}" for warning in report.ingestion_warnings)
        lines.append("")
    lines.append("Human review checklist:")
    lines.extend(f"- [ ] {item}" for item in report.human_review_checklist)
    return "\n".join(lines)


def overview_markdown(report: CreditReport) -> str:
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    manual_count = 0
    for flag in report.risk_flags:
        severity_counts[flag.severity] += 1
        manual_count += int(flag.manual_review_required)
    evidence_count = sum(len(flag.evidence) for flag in report.risk_flags)
    return f"""
<div class="summary-grid">
  <div class="summary-card">
    <div class="summary-label">Issuer</div>
    <div class="summary-value">{report.issuer_name}</div>
    <div class="summary-note">Synthetic sample or uploaded issuer profile</div>
  </div>
  <div class="summary-card">
    <div class="summary-label">Risk Flags</div>
    <div class="summary-value">{len(report.risk_flags)}</div>
    <div class="summary-note">{severity_counts["high"]} high / {severity_counts["medium"]} medium / {severity_counts["low"]} low</div>
  </div>
  <div class="summary-card">
    <div class="summary-label">Evidence Chunks</div>
    <div class="summary-value">{evidence_count}</div>
    <div class="summary-note">Retrieved from local source documents</div>
  </div>
  <div class="summary-card">
    <div class="summary-label">Manual Review</div>
    <div class="summary-value">{manual_count}</div>
    <div class="summary-note">Flags still requiring analyst evidence review</div>
  </div>
</div>
<div class="status-strip">
  Deterministic financial metrics and rule-based risk flags are the source of truth.
  This is a preliminary AI-generated credit analysis and requires human analyst review.
</div>
"""


def _empty_ui_result(message: str):
    return EMPTY_TABLE, EMPTY_TABLE, EMPTY_TABLE, message, "", ""


def _report_to_ui_result(report: CreditReport):
    return (
        metrics_table(report),
        risk_flags_table(report),
        evidence_table(report),
        overview_markdown(report),
        report.markdown,
        warnings_and_checklist(report),
    )


def run_credit_analysis_ui(issuer_file, financials_file, source_documents, use_llm_report: bool = False):
    if issuer_file is None or financials_file is None:
        return _empty_ui_result("Upload issuer profile JSON and financial CSV or Excel files, or click Run Sample Analysis.")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            issuer_path = _copy_upload(issuer_file, tmp_path)
            financials_path = _copy_upload(financials_file, tmp_path)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            for upload in source_documents or []:
                _copy_upload(upload, docs_dir)

            report = run_workflow(
                issuer_path=issuer_path,
                financials_path=financials_path,
                docs_path=docs_dir,
                use_llm_report=use_llm_report,
            )
            return _report_to_ui_result(report)
    except UserInputError as exc:
        return _empty_ui_result(f"Input error: {exc}")
    except Exception as exc:
        return _empty_ui_result(f"Unexpected error while running analysis: {exc}")


def run_sample_analysis_ui(use_llm_report: bool = False):
    try:
        report = run_workflow(
            issuer_path=SAMPLE_ISSUER,
            financials_path=SAMPLE_FINANCIALS,
            docs_path=SAMPLE_DOCS,
            use_llm_report=use_llm_report,
        )
        return _report_to_ui_result(report)
    except Exception as exc:
        return _empty_ui_result(f"Unexpected error while running sample analysis: {exc}")


def run_document_qa_ui(question: str, source_documents):
    try:
        if source_documents:
            with tempfile.TemporaryDirectory() as tmpdir:
                docs_dir = Path(tmpdir) / "docs"
                docs_dir.mkdir()
                for upload in source_documents:
                    _copy_upload(upload, docs_dir)
                answer, chunks = retrieve_question_evidence(question, docs_dir)
                return answer, qa_evidence_table(chunks)
        answer, chunks = retrieve_question_evidence(question, SAMPLE_DOCS)
        return answer, qa_evidence_table(chunks)
    except Exception as exc:
        return f"Unexpected error while retrieving evidence: {exc}", EMPTY_TABLE


def _copy_upload(upload, destination_dir: Path) -> Path:
    source = Path(getattr(upload, "name", upload))
    destination = destination_dir / source.name
    destination.write_bytes(source.read_bytes())
    return destination


def build_app():
    try:
        import gradio as gr
    except ImportError as exc:
        raise RuntimeError("gradio is required to launch the demo app. Install dependencies with pip install -r requirements.txt.") from exc

    with gr.Blocks(title="Bond Credit Due Diligence Agent") as demo:
        gr.HTML(
            """
            <div class="app-header">
              <h1>Bond Credit Due Diligence Agent</h1>
              <p>Deterministic credit metrics, rule-based risk detection, local evidence retrieval, and human-review-ready reporting.</p>
            </div>
            """
        )
        with gr.Row():
            with gr.Column(scale=1, min_width=320):
                gr.Markdown("### Analysis Inputs")
                issuer = gr.File(label="Issuer profile JSON", file_types=[".json"])
                financials = gr.File(label="Financial CSV or Excel", file_types=[".csv", ".xlsx"])
                docs = gr.File(label="Source documents", file_count="multiple", file_types=[".txt", ".md", ".pdf", ".csv", ".xlsx"])
                use_llm = gr.Checkbox(label="Optional LLM report polishing", value=False)
                qa_question = gr.Textbox(
                    label="Evidence Q&A",
                    placeholder="Ask about liquidity, leverage, cash flow, covenants, or revenue pressure...",
                    lines=3,
                )
                with gr.Row():
                    sample_button = gr.Button("Run Sample Analysis")
                    run_button = gr.Button("Run Credit Analysis", variant="primary")
                qa_button = gr.Button("Retrieve Evidence For Question")
                gr.Markdown(
                    "The sample workflow uses synthetic issuer data and local source documents. "
                    "LLM polishing is optional and never replaces calculated financial metrics."
                )
            with gr.Column(scale=3):
                overview = gr.HTML(label="Analysis Overview")
                with gr.Tabs():
                    with gr.Tab("Metrics"):
                        metrics = gr.Dataframe(label="Key Financial Metrics", interactive=False, wrap=True)
                    with gr.Tab("Risk Flags"):
                        risks = gr.Dataframe(label="Rule-Based Credit Risk Flags", interactive=False, wrap=True)
                    with gr.Tab("Evidence"):
                        evidence = gr.Dataframe(label="Retrieved Evidence", interactive=False, wrap=True)
                    with gr.Tab("Q&A"):
                        qa_answer = gr.Markdown(label="Evidence-Grounded Retrieval Result")
                        qa_sources = gr.Dataframe(label="Q&A Evidence Chunks", interactive=False, wrap=True)
                    with gr.Tab("Report"):
                        report = gr.Markdown(label="Markdown Credit Report")
                    with gr.Tab("Review"):
                        warnings = gr.Markdown(label="Warnings and Human Review Checklist")

        run_button.click(
            fn=run_credit_analysis_ui,
            inputs=[issuer, financials, docs, use_llm],
            outputs=[metrics, risks, evidence, overview, report, warnings],
        )
        sample_button.click(
            fn=run_sample_analysis_ui,
            inputs=[use_llm],
            outputs=[metrics, risks, evidence, overview, report, warnings],
        )
        qa_button.click(
            fn=run_document_qa_ui,
            inputs=[qa_question, docs],
            outputs=[qa_answer, qa_sources],
        )
    return demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the Bond Credit Due Diligence Agent Gradio app.")
    parser.add_argument(
        "--server-port",
        type=int,
        default=None,
        help="Port for the Gradio server. Defaults to the first available local port starting at 7860.",
    )
    args = parser.parse_args()
    server_port = args.server_port if args.server_port is not None else _find_available_port()
    build_app().launch(server_port=server_port, css=APP_CSS)


def _find_available_port(start: int = 7860, end: int = 9000) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise OSError(f"No available local port found in range {start}-{end}.")


if __name__ == "__main__":
    main()
