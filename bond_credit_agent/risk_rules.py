from __future__ import annotations

from bond_credit_agent.schemas import MetricResult, RiskFlag


def _value(metrics: dict[str, MetricResult], name: str) -> float | None:
    result = metrics.get(name)
    return result.value if result else None


def _flag(
    *,
    risk_type: str,
    severity: str,
    description: str,
    metric_name: str,
    metric_value: float,
    reasoning: str,
    recommendation: str,
    evidence_query: str,
) -> RiskFlag:
    return RiskFlag(
        risk_type=risk_type,
        severity=severity,  # type: ignore[arg-type]
        description=description,
        related_metric_values={metric_name: metric_value},
        reasoning=reasoning,
        recommendation=recommendation,
        evidence_query=evidence_query,
        manual_review_required=True,
    )


def detect_risks(metrics: dict[str, MetricResult]) -> list[RiskFlag]:
    flags: list[RiskFlag] = []

    debt_to_assets = _value(metrics, "debt_to_asset_ratio")
    if debt_to_assets is not None and debt_to_assets > 0.70:
        flags.append(
            _flag(
                risk_type="High leverage",
                severity="high",
                description="Debt-to-asset ratio exceeds the 0.70 threshold.",
                metric_name="debt_to_asset_ratio",
                metric_value=debt_to_assets,
                reasoning="High balance sheet leverage can reduce refinancing flexibility and loss absorption capacity.",
                recommendation="Review debt maturity schedule, covenant headroom, secured debt, and deleveraging plan.",
                evidence_query="leverage debt balance sheet refinancing covenant",
            )
        )

    current = _value(metrics, "current_ratio")
    if current is not None and current < 1.00:
        flags.append(
            _flag(
                risk_type="Weak liquidity",
                severity="high",
                description="Current ratio is below 1.00.",
                metric_name="current_ratio",
                metric_value=current,
                reasoning="Current assets may not fully cover current liabilities.",
                recommendation="Review liquidity sources, working capital facilities, and near-term maturities.",
                evidence_query="liquidity current liabilities working capital credit facility",
            )
        )

    cash_short_debt = _value(metrics, "cash_short_debt_ratio")
    if cash_short_debt is not None and cash_short_debt < 1.00:
        flags.append(
            _flag(
                risk_type="Short-term debt pressure",
                severity="high",
                description="Cash to short-term debt ratio is below 1.00.",
                metric_name="cash_short_debt_ratio",
                metric_value=cash_short_debt,
                reasoning="Cash on hand may be insufficient to repay short-term borrowings without refinancing.",
                recommendation="Confirm committed backup liquidity and upcoming refinancing actions.",
                evidence_query="short-term debt cash refinancing maturity liquidity",
            )
        )

    ocf_to_debt = _value(metrics, "operating_cash_flow_to_debt")
    if ocf_to_debt is not None and ocf_to_debt < 0.05:
        flags.append(
            _flag(
                risk_type="Weak operating cash flow",
                severity="medium",
                description="Operating cash flow to debt is below 0.05.",
                metric_name="operating_cash_flow_to_debt",
                metric_value=ocf_to_debt,
                reasoning="Internal cash generation is weak relative to debt obligations.",
                recommendation="Review cash conversion, capital expenditure needs, and one-off working capital effects.",
                evidence_query="operating cash flow debt cash generation working capital",
            )
        )

    coverage = _value(metrics, "interest_coverage_ratio")
    if coverage is not None and coverage < 1.50:
        flags.append(
            _flag(
                risk_type="Weak interest coverage",
                severity="high",
                description="Interest coverage ratio is below 1.50.",
                metric_name="interest_coverage_ratio",
                metric_value=coverage,
                reasoning="EBIT provides limited cushion for interest expense.",
                recommendation="Review interest rate exposure, debt repricing, and earnings sensitivity.",
                evidence_query="interest coverage EBIT interest expense rates",
            )
        )

    revenue = _value(metrics, "revenue_growth")
    if revenue is not None and revenue < -0.10:
        flags.append(
            _flag(
                risk_type="Revenue decline",
                severity="medium",
                description="Revenue declined by more than 10 percent year over year.",
                metric_name="revenue_growth",
                metric_value=revenue,
                reasoning="Revenue contraction can weaken profitability and debt service capacity.",
                recommendation="Review demand trends, customer concentration, and management's revenue stabilization plan.",
                evidence_query="revenue decline demand customer concentration sales",
            )
        )

    margin = _value(metrics, "net_profit_margin")
    if margin is not None and margin < 0:
        flags.append(
            _flag(
                risk_type="Profitability pressure",
                severity="medium",
                description="Net profit margin is negative.",
                metric_name="net_profit_margin",
                metric_value=margin,
                reasoning="Loss-making operations may pressure retained cash flow and balance sheet flexibility.",
                recommendation="Review drivers of losses, restructuring costs, and expected margin recovery.",
                evidence_query="profitability net loss margin restructuring cost pressure",
            )
        )

    debt_growth = _value(metrics, "total_debt_growth")
    if debt_growth is not None and debt_growth > 0.20:
        flags.append(
            _flag(
                risk_type="Debt expansion pressure",
                severity="medium",
                description="Total interest-bearing debt increased by more than 20 percent year over year.",
                metric_name="total_debt_growth",
                metric_value=debt_growth,
                reasoning="Rapid debt growth can signal acquisition, liquidity, or refinancing pressure.",
                recommendation="Review use of proceeds, debt maturity profile, and expected deleveraging.",
                evidence_query="debt increased expansion acquisition proceeds deleveraging",
            )
        )

    return flags
