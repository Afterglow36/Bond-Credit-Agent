from bond_credit_agent.prompt_templates import build_rag_prompt
from bond_credit_agent.qa import retrieve_question_evidence


def test_prompt_template_is_constrained():
    prompt = build_rag_prompt("debt_service_capacity", "What is the liquidity risk?", "Evidence text")

    assert "Do not create new facts" in prompt
    assert "What is the liquidity risk?" in prompt


def test_retrieve_question_evidence_returns_sources():
    answer, chunks = retrieve_question_evidence("liquidity refinancing debt", "data/sample")

    assert "retrieval output" in answer
    assert chunks
