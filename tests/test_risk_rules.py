from bond_credit_agent.financial_metrics import calculate_all_metrics, load_financials
from bond_credit_agent.risk_rules import detect_risks


def test_risk_rules_trigger_on_sample_data():
    metrics = calculate_all_metrics(load_financials("data/sample/financials_sample.csv"))

    flags = detect_risks(metrics)
    risk_types = {flag.risk_type for flag in flags}

    assert "High leverage" in risk_types
    assert "Weak liquidity" in risk_types
    assert "Short-term debt pressure" in risk_types
    assert "Weak operating cash flow" in risk_types
    assert "Weak interest coverage" in risk_types
    assert "Revenue decline" in risk_types
    assert "Profitability pressure" in risk_types
    assert "Debt expansion pressure" in risk_types
    assert all(flag.related_metric_values for flag in flags)
