from __future__ import annotations


PROMPT_TEMPLATES = {
    "company_fundamentals": "Summarize issuer fundamentals using only retrieved evidence and issuer profile fields.",
    "debt_service_capacity": "Analyze liquidity, interest coverage, cash flow, and near-term debt pressure using calculated metrics.",
    "cash_flow_quality": "Identify cash conversion, working capital, and operating cash flow risks grounded in evidence.",
    "liability_structure": "Review short-term debt, long-term debt, refinancing needs, covenants, and leverage.",
    "operating_risk": "Review revenue trends, customer demand, margin pressure, and operating performance risks.",
}


def build_rag_prompt(template_name: str, query: str, evidence: str) -> str:
    """Build a constrained prompt for future LangChain or LLM integrations."""
    template = PROMPT_TEMPLATES.get(template_name)
    if template is None:
        raise ValueError(f"Unknown prompt template: {template_name}")
    return (
        f"{template}\n\n"
        "Use only the provided evidence. Do not create new facts, ratings, figures, or conclusions.\n\n"
        f"Question: {query}\n\n"
        f"Evidence:\n{evidence}"
    )
