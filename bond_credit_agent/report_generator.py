from __future__ import annotations

from bond_credit_agent.llm_report import maybe_polish_report_with_llm
from bond_credit_agent.schemas import CreditAnalysisState


DISCLAIMER = "This is an AI-generated preliminary credit analysis and requires human analyst review."


def _format_value(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.4f}"


def _escape_table(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ")


def generate_markdown_report(state: CreditAnalysisState, *, use_llm: bool = False) -> str:
    if state.issuer_profile is None:
        raise ValueError("Issuer profile is required to generate a report.")

    issuer = state.issuer_profile
    lines: list[str] = [
        f"# Preliminary Credit Risk Report: {issuer.issuer_name}",
        "",
        f"**{DISCLAIMER}**",
        "",
        "## Executive Summary",
        "",
        (
            f"{issuer.issuer_name} has {len(state.risk_flags)} calculated risk flag(s) based on the supplied "
            "synthetic financial statements and parsed local source documents."
        ),
        "",
        "## Issuer Overview",
        "",
        f"- Industry: {issuer.industry}",
        f"- Headquarters: {issuer.headquarters}",
        f"- Bond: {issuer.bond_description}",
        f"- Currency: {issuer.currency}",
        f"- Business summary: {issuer.business_summary}",
        "",
        "## Key Financial Metrics",
        "",
        "| Metric | Year | Value | Calculation Note |",
        "| --- | ---: | ---: | --- |",
    ]

    for metric in state.metrics.values():
        year = str(metric.year) if metric.year is not None else "N/A"
        lines.append(f"| {metric.name} | {year} | {_format_value(metric.value)} | {metric.explanation} |")

    if state.ingestion_warnings:
        lines.extend(["", "## Document Ingestion Warnings", ""])
        for warning in state.ingestion_warnings:
            lines.append(f"- {warning}")

    lines.extend(
        [
            "",
            "## Risk Flag Table",
            "",
            "| Risk Type | Severity | Metric Values | Evidence Status | Manual Review |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    if not state.risk_flags:
        lines.append("| None | N/A | N/A | No rule-based risk flags were triggered. | No |")
    else:
        for flag in state.risk_flags:
            metrics = ", ".join(f"{name}={_format_value(value)}" for name, value in flag.related_metric_values.items())
            manual = "Yes" if flag.manual_review_required else "No"
            lines.append(
                f"| {flag.risk_type} | {flag.severity} | {_escape_table(metrics)} | "
                f"{_escape_table(flag.evidence_summary)} | {manual} |"
            )

    lines.extend(["", "## Risk Flag Details", ""])
    if not state.risk_flags:
        lines.append("No rule-based risk flags were triggered by calculated metrics.")
    else:
        for flag in state.risk_flags:
            metrics = ", ".join(f"{name}={_format_value(value)}" for name, value in flag.related_metric_values.items())
            lines.extend(
                [
                    f"### {flag.risk_type} ({flag.severity})",
                    "",
                    f"- Description: {flag.description}",
                    f"- Metric values: {metrics}",
                    f"- Reasoning: {flag.reasoning}",
                    f"- Recommendation: {flag.recommendation}",
                    f"- Evidence status: {flag.evidence_summary}",
                    f"- Manual review required: {'Yes' if flag.manual_review_required else 'No'}",
                    "",
                ]
            )

    lines.extend(
        [
            "## Evidence Table",
            "",
            "| Risk Type | Source File | Page | Chunk ID | Evidence Excerpt |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    evidence_rows = 0
    for flag in state.risk_flags:
        for chunk in flag.evidence:
            excerpt = _escape_table(chunk.text)
            page = str(chunk.page_number) if chunk.page_number is not None else "N/A"
            lines.append(f"| {flag.risk_type} | {chunk.source_file} | {page} | {chunk.chunk_id} | {excerpt} |")
            evidence_rows += 1
    if evidence_rows == 0:
        lines.append("| Manual review | N/A | N/A | N/A | No supporting evidence retrieved. |")

    lines.extend(["", "## Human Review Checklist", ""])
    for item in state.human_review_checklist:
        lines.append(f"- [ ] {item}")

    lines.extend(
        [
            "",
            "## Preliminary Credit Opinion",
            "",
            _preliminary_opinion(state),
            "",
            "## Limitations",
            "",
            "- This MVP uses synthetic sample data only.",
            "- It does not provide an investment recommendation.",
            "- Risk flags are deterministic and rule-based.",
            "- Evidence retrieval is local TF-IDF with keyword fallback and may miss relevant language.",
            "- Optional LLM report polishing, when enabled, must not change calculated metrics or add new facts.",
            f"- {DISCLAIMER}",
        ]
    )
    template_markdown = "\n".join(lines) + "\n"
    if not use_llm:
        return template_markdown

    polished_markdown, status = maybe_polish_report_with_llm(state, template_markdown)
    if status:
        state.ingestion_warnings.append(status)
    return polished_markdown


def _preliminary_opinion(state: CreditAnalysisState) -> str:
    high_count = sum(1 for flag in state.risk_flags if flag.severity == "high")
    medium_count = sum(1 for flag in state.risk_flags if flag.severity == "medium")
    if high_count >= 3:
        return "Preliminary view: elevated credit risk due to multiple high-severity leverage, liquidity, or coverage concerns."
    if high_count:
        return "Preliminary view: heightened credit risk due to at least one high-severity risk flag."
    if medium_count:
        return "Preliminary view: moderate credit risk indicators require analyst follow-up."
    return "Preliminary view: no material rule-based credit stress indicators were triggered by the supplied data."
