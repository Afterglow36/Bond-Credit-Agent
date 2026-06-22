from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class IssuerProfile(BaseModel):
    issuer_name: str
    industry: str
    headquarters: str
    bond_description: str
    currency: str
    business_summary: str


class MetricResult(BaseModel):
    name: str
    value: float | None
    year: int | None = None
    explanation: str


class EvidenceChunk(BaseModel):
    source_file: str
    chunk_id: int
    text: str
    page_number: int | None = None
    score: float = 0.0


class RiskFlag(BaseModel):
    risk_type: str
    severity: Literal["low", "medium", "high"]
    description: str
    related_metric_values: dict[str, float | None]
    reasoning: str
    recommendation: str
    evidence_query: str
    manual_review_required: bool = True
    evidence_summary: str = "No evidence retrieved yet."
    evidence: list[EvidenceChunk] = Field(default_factory=list)


class CreditAnalysisState(BaseModel):
    issuer_profile: IssuerProfile | None = None
    financial_rows: list[dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, MetricResult] = Field(default_factory=dict)
    document_chunks: list[EvidenceChunk] = Field(default_factory=list)
    ingestion_warnings: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    evidence_chunks: list[EvidenceChunk] = Field(default_factory=list)
    human_review_checklist: list[str] = Field(default_factory=list)
    report_markdown: str | None = None


class CreditReport(BaseModel):
    issuer_name: str
    metrics: dict[str, MetricResult]
    risk_flags: list[RiskFlag]
    evidence_chunks: list[EvidenceChunk]
    human_review_checklist: list[str]
    ingestion_warnings: list[str] = Field(default_factory=list)
    markdown: str
