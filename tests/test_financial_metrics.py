import pandas as pd

from bond_credit_agent.financial_metrics import calculate_all_metrics, current_ratio, debt_to_asset_ratio


def test_financial_metric_calculations_use_latest_year():
    df = pd.DataFrame(
        [
            {
                "year": 2024,
                "total_assets": 100,
                "total_liabilities": 60,
                "current_assets": 50,
                "current_liabilities": 25,
                "cash_and_cash_equivalents": 20,
                "short_term_debt": 10,
                "long_term_debt": 40,
                "operating_cash_flow": 10,
                "ebit": 30,
                "interest_expense": 10,
                "revenue": 100,
                "net_profit": 5,
            },
            {
                "year": 2025,
                "total_assets": 100,
                "total_liabilities": 75,
                "current_assets": 40,
                "current_liabilities": 50,
                "cash_and_cash_equivalents": 15,
                "short_term_debt": 30,
                "long_term_debt": 50,
                "operating_cash_flow": 4,
                "ebit": 12,
                "interest_expense": 10,
                "revenue": 80,
                "net_profit": -4,
            },
        ]
    )

    metrics = calculate_all_metrics(df)

    assert metrics["debt_to_asset_ratio"].value == 0.75
    assert metrics["current_ratio"].value == 0.8
    assert metrics["cash_short_debt_ratio"].value == 0.5
    assert metrics["total_interest_bearing_debt"].value == 80
    assert metrics["operating_cash_flow_to_debt"].value == 0.05
    assert metrics["interest_coverage_ratio"].value == 1.2
    assert metrics["revenue_growth"].value == -0.2
    assert metrics["net_profit_margin"].value == -0.05
    assert metrics["total_debt_growth"].value == 0.6


def test_zero_denominator_returns_none_with_explanation():
    df = pd.DataFrame([{"year": 2025, "total_assets": 0, "total_liabilities": 10}])

    metric = debt_to_asset_ratio(df)

    assert metric.value is None
    assert "zero" in metric.explanation


def test_missing_value_returns_none_with_explanation():
    df = pd.DataFrame([{"year": 2025, "current_assets": 10}])

    metric = current_ratio(df)

    assert metric.value is None
    assert "missing" in metric.explanation
