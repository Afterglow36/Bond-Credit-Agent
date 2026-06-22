from bond_credit_agent.app import (
    evidence_table,
    metrics_table,
    overview_markdown,
    risk_flags_table,
    run_document_qa_ui,
    run_credit_analysis_ui,
    run_sample_analysis_ui,
    warnings_and_checklist,
)
from bond_credit_agent.workflow import run_workflow


def test_gradio_helper_tables_are_generated():
    report = run_workflow(
        issuer_path="data/sample/issuer_profile_sample.json",
        financials_path="data/sample/financials_sample.csv",
        docs_path="data/sample",
    )

    assert not metrics_table(report).empty
    assert not risk_flags_table(report).empty
    assert not evidence_table(report).empty
    assert "summary-card" in overview_markdown(report)
    assert "Human review checklist" in warnings_and_checklist(report)


def test_sample_analysis_ui_returns_visual_outputs():
    metrics, risks, evidence, overview, report, review = run_sample_analysis_ui(False)

    assert not metrics.empty
    assert not risks.empty
    assert not evidence.empty
    assert "Risk Flags" in overview
    assert "Preliminary Credit Risk Report" in report
    assert "Human review checklist" in review


def test_upload_analysis_ui_empty_state_has_six_outputs():
    result = run_credit_analysis_ui(None, None, None, False)

    assert len(result) == 6
    assert "Upload issuer profile" in result[3]


def test_document_qa_ui_uses_sample_docs_when_no_uploads():
    answer, chunks = run_document_qa_ui("What does the evidence say about liquidity?", None)

    assert "Evidence-grounded retrieval result" in answer
    assert not chunks.empty
