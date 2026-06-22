from bond_credit_agent.llm_report import LLM_SAFETY_INSTRUCTION, maybe_polish_report_with_llm
from bond_credit_agent.report_generator import generate_markdown_report
from bond_credit_agent.workflow import calculate_metrics, detect_risk_flags, human_review_checklist, load_inputs, parse_source_documents, retrieve_evidence


def _sample_state():
    state = load_inputs("data/sample/issuer_profile_sample.json", "data/sample/financials_sample.csv")
    state = parse_source_documents(state, "data/sample")
    state = calculate_metrics(state)
    state = detect_risk_flags(state)
    state = retrieve_evidence(state, "data/sample")
    return human_review_checklist(state)


def test_report_generation_contains_professional_sections():
    report = generate_markdown_report(_sample_state())

    assert "## Executive Summary" in report
    assert "## Risk Flag Table" in report
    assert "## Evidence Table" in report
    assert "## Human Review Checklist" in report
    assert "AI-generated preliminary credit analysis" in report


def test_llm_fallback_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    template = "template report"

    output, status = maybe_polish_report_with_llm(_sample_state(), template)

    assert output == template
    assert "OPENAI_API_KEY is not set" in status
    assert "Do not create new facts" in LLM_SAFETY_INSTRUCTION
