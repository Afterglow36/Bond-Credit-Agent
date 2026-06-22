from __future__ import annotations

import os

from bond_credit_agent.schemas import CreditAnalysisState


LLM_SAFETY_INSTRUCTION = (
    "Use only the provided issuer profile, calculated metrics, risk flags, and evidence. "
    "Do not create new facts, ratings, figures, or conclusions."
)


def maybe_polish_report_with_llm(state: CreditAnalysisState, template_markdown: str) -> tuple[str, str | None]:
    """Optionally polish report wording with an LLM, falling back to the template on any issue."""
    if not os.environ.get("OPENAI_API_KEY"):
        return template_markdown, "LLM polishing skipped because OPENAI_API_KEY is not set."

    try:
        from openai import OpenAI
    except Exception as exc:
        return template_markdown, f"LLM polishing skipped because the OpenAI SDK is unavailable: {exc}"

    try:
        client = OpenAI()
        response = client.responses.create(
            model=os.environ.get("OPENAI_REPORT_MODEL", "gpt-4.1-mini"),
            instructions=(
                "You are polishing a preliminary bond credit analysis report for clarity and formatting. "
                f"{LLM_SAFETY_INSTRUCTION} Preserve all numeric values exactly. Preserve the human review disclaimer."
            ),
            input=_build_llm_input(state, template_markdown),
            max_output_tokens=2500,
        )
        polished = getattr(response, "output_text", "") or ""
        if not polished.strip():
            return template_markdown, "LLM polishing returned no text; template report was used."
        return polished.strip() + "\n", "LLM polishing applied with deterministic metrics retained as source of truth."
    except Exception as exc:
        return template_markdown, f"LLM polishing failed and template report was used: {exc}"


def _build_llm_input(state: CreditAnalysisState, template_markdown: str) -> str:
    issuer = state.issuer_profile.model_dump() if state.issuer_profile else {}
    metrics = {name: metric.model_dump() for name, metric in state.metrics.items()}
    risk_flags = [
        {
            "risk_type": flag.risk_type,
            "severity": flag.severity,
            "related_metric_values": flag.related_metric_values,
            "reasoning": flag.reasoning,
            "recommendation": flag.recommendation,
            "manual_review_required": flag.manual_review_required,
            "evidence_summary": flag.evidence_summary,
            "evidence": [chunk.model_dump() for chunk in flag.evidence],
        }
        for flag in state.risk_flags
    ]
    return (
        f"{LLM_SAFETY_INSTRUCTION}\n\n"
        f"Issuer profile:\n{issuer}\n\n"
        f"Calculated metrics:\n{metrics}\n\n"
        f"Risk flags and retrieved evidence:\n{risk_flags}\n\n"
        "Polish the markdown below for readability without adding facts or changing numbers:\n\n"
        f"{template_markdown}"
    )
