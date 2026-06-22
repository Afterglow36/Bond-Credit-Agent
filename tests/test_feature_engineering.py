from bond_credit_agent.feature_engineering import build_credit_feature_frame, deterministic_risk_signal_columns


def test_feature_engineering_exposes_metric_features():
    features = build_credit_feature_frame("data/sample/financials_sample.csv")
    signals = deterministic_risk_signal_columns(features)

    assert "debt_to_asset_ratio" in features.columns
    assert features.loc[0, "debt_to_asset_ratio"] > 0.70
    assert bool(signals.loc[0, "high_leverage_signal"]) is True
    assert bool(signals.loc[0, "weak_liquidity_signal"]) is True
