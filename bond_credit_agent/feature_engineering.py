from __future__ import annotations

from typing import Any

import pandas as pd

from bond_credit_agent.financial_metrics import calculate_all_metrics, load_financials


FEATURE_COLUMNS = [
    "debt_to_asset_ratio",
    "current_ratio",
    "cash_short_debt_ratio",
    "total_interest_bearing_debt",
    "operating_cash_flow_to_debt",
    "interest_coverage_ratio",
    "revenue_growth",
    "net_profit_margin",
    "total_debt_growth",
]


def build_credit_feature_frame(financials: str | pd.DataFrame | list[dict[str, Any]]) -> pd.DataFrame:
    """Build one deterministic feature row suitable for future model adapters.

    This does not train a model or fabricate labels. It exposes calculated financial
    metrics in a tabular form that could later feed a vetted Scikit-learn/XGBoost
    model if real labeled data becomes available.
    """
    if isinstance(financials, str):
        metrics = calculate_all_metrics(load_financials(financials))
    else:
        metrics = calculate_all_metrics(financials)
    row = {name: metrics[name].value for name in FEATURE_COLUMNS}
    return pd.DataFrame([row], columns=FEATURE_COLUMNS)


def deterministic_risk_signal_columns(feature_frame: pd.DataFrame) -> pd.DataFrame:
    """Create transparent binary signal columns from the same thresholds as the rule engine."""
    signals = pd.DataFrame(index=feature_frame.index)
    signals["high_leverage_signal"] = feature_frame["debt_to_asset_ratio"] > 0.70
    signals["weak_liquidity_signal"] = feature_frame["current_ratio"] < 1.00
    signals["short_debt_pressure_signal"] = feature_frame["cash_short_debt_ratio"] < 1.00
    signals["weak_cash_flow_signal"] = feature_frame["operating_cash_flow_to_debt"] < 0.05
    signals["weak_interest_coverage_signal"] = feature_frame["interest_coverage_ratio"] < 1.50
    signals["revenue_decline_signal"] = feature_frame["revenue_growth"] < -0.10
    signals["negative_margin_signal"] = feature_frame["net_profit_margin"] < 0
    signals["debt_growth_signal"] = feature_frame["total_debt_growth"] > 0.20
    return signals.fillna(False)
