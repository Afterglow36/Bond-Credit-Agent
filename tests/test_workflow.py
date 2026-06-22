from pathlib import Path

from bond_credit_agent.workflow import run_workflow


def test_end_to_end_workflow_generates_report(tmp_path):
    output = tmp_path / "report.md"

    report = run_workflow(
        issuer_path="data/sample/issuer_profile_sample.json",
        financials_path="data/sample/financials_sample.csv",
        docs_path="data/sample",
        output_path=output,
    )

    assert output.exists()
    assert report.risk_flags
    assert report.evidence_chunks
    assert all(flag.evidence_summary for flag in report.risk_flags)
    assert "Human Review Checklist" in report.markdown
    assert "AI-generated preliminary credit analysis" in report.markdown
    assert "| Risk Type | Source File | Page | Chunk ID | Evidence Excerpt |" in report.markdown
    assert Path(output).read_text(encoding="utf-8") == report.markdown


def test_workflow_marks_risks_for_manual_review_without_evidence(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "unrelated.txt").write_text("This document discusses office furniture.", encoding="utf-8")

    report = run_workflow(
        issuer_path="data/sample/issuer_profile_sample.json",
        financials_path="data/sample/financials_sample.csv",
        docs_path=docs,
    )

    assert report.risk_flags
    assert all(flag.manual_review_required for flag in report.risk_flags)
    assert "manual analyst review is required" in report.risk_flags[0].evidence_summary
