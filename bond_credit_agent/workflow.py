from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from bond_credit_agent.exceptions import UserInputError
from bond_credit_agent.financial_metrics import calculate_all_metrics, load_financials
from bond_credit_agent.ingestion import parse_documents
from bond_credit_agent.report_generator import generate_markdown_report
from bond_credit_agent.retriever import LocalEvidenceRetriever
from bond_credit_agent.risk_rules import detect_risks
from bond_credit_agent.schemas import CreditAnalysisState, CreditReport, IssuerProfile


def load_inputs(issuer_path: str | Path, financials_path: str | Path) -> CreditAnalysisState:
    issuer_path = Path(issuer_path)
    if not issuer_path.exists():
        raise UserInputError(f"Issuer profile file not found: {issuer_path}")
    if issuer_path.stat().st_size == 0:
        raise UserInputError(f"Issuer profile file is empty: {issuer_path.name}")
    try:
        issuer_data = json.loads(issuer_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise UserInputError(f"Issuer profile must be valid JSON: {exc.msg}") from exc
    try:
        issuer_profile = IssuerProfile(**issuer_data)
    except ValidationError as exc:
        missing = [str(".".join(map(str, error["loc"]))) for error in exc.errors() if error["type"] == "missing"]
        if missing:
            raise UserInputError(f"Issuer profile missing required fields: {missing}") from exc
        raise UserInputError(f"Issuer profile is invalid: {exc}") from exc
    financials = load_financials(financials_path)
    return CreditAnalysisState(
        issuer_profile=issuer_profile,
        financial_rows=financials.to_dict(orient="records"),
    )


def calculate_metrics(state: CreditAnalysisState) -> CreditAnalysisState:
    state.metrics = calculate_all_metrics(pd.DataFrame(state.financial_rows))
    return state


def parse_source_documents(state: CreditAnalysisState, docs_path: str | Path) -> CreditAnalysisState:
    chunks, warnings = parse_documents(docs_path)
    state.document_chunks = chunks
    state.ingestion_warnings = warnings
    return state


def detect_risk_flags(state: CreditAnalysisState) -> CreditAnalysisState:
    state.risk_flags = detect_risks(state.metrics)
    return state


def retrieve_evidence(state: CreditAnalysisState, docs_path: str | Path, top_k: int = 2) -> CreditAnalysisState:
    if not state.document_chunks:
        state = parse_source_documents(state, docs_path)
    retriever = LocalEvidenceRetriever(chunks=state.document_chunks)
    evidence_chunks = []
    for index, flag in enumerate(state.risk_flags):
        chunks = retriever.retrieve(flag.evidence_query, top_k=top_k)
        flag.evidence = chunks
        flag.manual_review_required = len(chunks) == 0
        if chunks:
            sources = sorted({chunk.source_file for chunk in chunks})
            flag.evidence_summary = f"Retrieved {len(chunks)} supporting chunk(s) from {', '.join(sources)}."
        else:
            flag.evidence_summary = "No supporting evidence was retrieved; manual analyst review is required."
        state.risk_flags[index] = flag
        evidence_chunks.extend(chunks)
    state.evidence_chunks = evidence_chunks
    return state


def human_review_checklist(state: CreditAnalysisState) -> CreditAnalysisState:
    checklist = [
        "Confirm all input financial statement numbers against source filings.",
        "Review debt maturity schedule, secured debt, and covenant package.",
        "Assess liquidity sources, committed facilities, and refinancing plan.",
        "Validate whether retrieved evidence supports each triggered risk flag.",
        "Document any risks requiring manual review due to missing or weak evidence.",
    ]
    for flag in state.risk_flags:
        if flag.manual_review_required:
            checklist.append(f"Manually review evidence for risk flag: {flag.risk_type}.")
    state.human_review_checklist = checklist
    return state


def generate_report(state: CreditAnalysisState, *, use_llm_report: bool = False) -> CreditAnalysisState:
    state.report_markdown = generate_markdown_report(state, use_llm=use_llm_report)
    return state


def run_workflow(
    *,
    issuer_path: str | Path,
    financials_path: str | Path,
    docs_path: str | Path,
    output_path: str | Path | None = None,
    use_llm_report: bool = False,
) -> CreditReport:
    state = load_inputs(issuer_path, financials_path)
    state = parse_source_documents(state, docs_path)
    state = calculate_metrics(state)
    state = detect_risk_flags(state)
    state = retrieve_evidence(state, docs_path)
    state = human_review_checklist(state)
    state = generate_report(state, use_llm_report=use_llm_report)

    if state.issuer_profile is None or state.report_markdown is None:
        raise ValueError("Workflow did not produce a complete report.")

    if output_path is not None:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(state.report_markdown, encoding="utf-8")

    return CreditReport(
        issuer_name=state.issuer_profile.issuer_name,
        metrics=state.metrics,
        risk_flags=state.risk_flags,
        evidence_chunks=state.evidence_chunks,
        human_review_checklist=state.human_review_checklist,
        ingestion_warnings=state.ingestion_warnings,
        markdown=state.report_markdown,
    )
