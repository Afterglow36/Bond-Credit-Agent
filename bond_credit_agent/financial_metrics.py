from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from bond_credit_agent.exceptions import UserInputError
from bond_credit_agent.schemas import MetricResult


REQUIRED_COLUMNS = {
    "year",
    "total_assets",
    "total_liabilities",
    "current_assets",
    "current_liabilities",
    "cash_and_cash_equivalents",
    "short_term_debt",
    "long_term_debt",
    "operating_cash_flow",
    "ebit",
    "interest_expense",
    "revenue",
    "net_profit",
}


def load_financials(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise UserInputError(f"Financial file not found: {path}")
    if path.stat().st_size == 0:
        raise UserInputError(f"Financial file is empty: {path.name}")
    if path.suffix.lower() not in {".csv", ".xlsx"}:
        raise UserInputError("Financial file must be a .csv or .xlsx file.")
    try:
        if path.suffix.lower() == ".xlsx":
            df = pd.read_excel(path)
        else:
            df = pd.read_csv(path)
    except Exception as exc:
        raise UserInputError(f"Could not read financial file {path.name}: {exc}") from exc
    if df.empty:
        raise UserInputError(f"Financial file has no data rows: {path.name}")
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise UserInputError(f"Financial file missing required columns: {sorted(missing)}")
    numeric_columns = REQUIRED_COLUMNS - {"year"}
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df.sort_values("year").reset_index(drop=True)


def _metric(name: str, value: float | None, year: int | None, explanation: str) -> MetricResult:
    return MetricResult(name=name, value=value, year=year, explanation=explanation)


def _latest_row(df: pd.DataFrame) -> tuple[pd.Series | None, int | None, str | None]:
    if df.empty:
        return None, None, "Financial data is empty."
    row = df.sort_values("year").iloc[-1]
    year = None if pd.isna(row.get("year")) else int(row["year"])
    return row, year, None


def _value(row: pd.Series, column: str) -> float | None:
    if column not in row or pd.isna(row[column]):
        return None
    return float(row[column])


def _safe_ratio(
    *,
    name: str,
    numerator: float | None,
    denominator: float | None,
    year: int | None,
    numerator_label: str,
    denominator_label: str,
) -> MetricResult:
    if numerator is None:
        return _metric(name, None, year, f"Cannot calculate because {numerator_label} is missing.")
    if denominator is None:
        return _metric(name, None, year, f"Cannot calculate because {denominator_label} is missing.")
    if denominator == 0:
        return _metric(name, None, year, f"Cannot calculate because {denominator_label} is zero.")
    return _metric(name, numerator / denominator, year, "Calculated from financial statement inputs.")


def debt_to_asset_ratio(df: pd.DataFrame) -> MetricResult:
    row, year, error = _latest_row(df)
    if error:
        return _metric("debt_to_asset_ratio", None, year, error)
    return _safe_ratio(
        name="debt_to_asset_ratio",
        numerator=_value(row, "total_liabilities"),
        denominator=_value(row, "total_assets"),
        year=year,
        numerator_label="total_liabilities",
        denominator_label="total_assets",
    )


def current_ratio(df: pd.DataFrame) -> MetricResult:
    row, year, error = _latest_row(df)
    if error:
        return _metric("current_ratio", None, year, error)
    return _safe_ratio(
        name="current_ratio",
        numerator=_value(row, "current_assets"),
        denominator=_value(row, "current_liabilities"),
        year=year,
        numerator_label="current_assets",
        denominator_label="current_liabilities",
    )


def cash_short_debt_ratio(df: pd.DataFrame) -> MetricResult:
    row, year, error = _latest_row(df)
    if error:
        return _metric("cash_short_debt_ratio", None, year, error)
    return _safe_ratio(
        name="cash_short_debt_ratio",
        numerator=_value(row, "cash_and_cash_equivalents"),
        denominator=_value(row, "short_term_debt"),
        year=year,
        numerator_label="cash_and_cash_equivalents",
        denominator_label="short_term_debt",
    )


def total_interest_bearing_debt(df: pd.DataFrame) -> MetricResult:
    row, year, error = _latest_row(df)
    if error:
        return _metric("total_interest_bearing_debt", None, year, error)
    short_term_debt = _value(row, "short_term_debt")
    long_term_debt = _value(row, "long_term_debt")
    if short_term_debt is None or long_term_debt is None:
        return _metric(
            "total_interest_bearing_debt",
            None,
            year,
            "Cannot calculate because short_term_debt or long_term_debt is missing.",
        )
    return _metric(
        "total_interest_bearing_debt",
        short_term_debt + long_term_debt,
        year,
        "Calculated as short_term_debt plus long_term_debt.",
    )


def operating_cash_flow_to_debt(df: pd.DataFrame) -> MetricResult:
    row, year, error = _latest_row(df)
    if error:
        return _metric("operating_cash_flow_to_debt", None, year, error)
    debt = total_interest_bearing_debt(df).value
    return _safe_ratio(
        name="operating_cash_flow_to_debt",
        numerator=_value(row, "operating_cash_flow"),
        denominator=debt,
        year=year,
        numerator_label="operating_cash_flow",
        denominator_label="total_interest_bearing_debt",
    )


def interest_coverage_ratio(df: pd.DataFrame) -> MetricResult:
    row, year, error = _latest_row(df)
    if error:
        return _metric("interest_coverage_ratio", None, year, error)
    return _safe_ratio(
        name="interest_coverage_ratio",
        numerator=_value(row, "ebit"),
        denominator=_value(row, "interest_expense"),
        year=year,
        numerator_label="ebit",
        denominator_label="interest_expense",
    )


def _latest_growth(df: pd.DataFrame, column: str, name: str) -> MetricResult:
    if len(df) < 2:
        return _metric(name, None, None, f"Cannot calculate because at least two years of {column} are required.")
    ordered = df.sort_values("year").reset_index(drop=True)
    latest = ordered.iloc[-1]
    previous = ordered.iloc[-2]
    year = None if pd.isna(latest.get("year")) else int(latest["year"])
    latest_value = _value(latest, column)
    previous_value = _value(previous, column)
    if latest_value is None:
        return _metric(name, None, year, f"Cannot calculate because latest {column} is missing.")
    if previous_value is None:
        return _metric(name, None, year, f"Cannot calculate because prior-year {column} is missing.")
    if previous_value == 0:
        return _metric(name, None, year, f"Cannot calculate because prior-year {column} is zero.")
    return _metric(name, (latest_value - previous_value) / previous_value, year, "Calculated as latest year-over-year growth.")


def revenue_growth(df: pd.DataFrame) -> MetricResult:
    return _latest_growth(df, "revenue", "revenue_growth")


def net_profit_margin(df: pd.DataFrame) -> MetricResult:
    row, year, error = _latest_row(df)
    if error:
        return _metric("net_profit_margin", None, year, error)
    return _safe_ratio(
        name="net_profit_margin",
        numerator=_value(row, "net_profit"),
        denominator=_value(row, "revenue"),
        year=year,
        numerator_label="net_profit",
        denominator_label="revenue",
    )


def total_debt_growth(df: pd.DataFrame) -> MetricResult:
    if len(df) < 2:
        return _metric("total_debt_growth", None, None, "Cannot calculate because at least two years are required.")
    ordered = df.sort_values("year").reset_index(drop=True).copy()
    ordered["total_interest_bearing_debt"] = ordered["short_term_debt"] + ordered["long_term_debt"]
    return _latest_growth(ordered, "total_interest_bearing_debt", "total_debt_growth")


METRIC_FUNCTIONS: dict[str, Callable[[pd.DataFrame], MetricResult]] = {
    "debt_to_asset_ratio": debt_to_asset_ratio,
    "current_ratio": current_ratio,
    "cash_short_debt_ratio": cash_short_debt_ratio,
    "total_interest_bearing_debt": total_interest_bearing_debt,
    "operating_cash_flow_to_debt": operating_cash_flow_to_debt,
    "interest_coverage_ratio": interest_coverage_ratio,
    "revenue_growth": revenue_growth,
    "net_profit_margin": net_profit_margin,
    "total_debt_growth": total_debt_growth,
}


def calculate_all_metrics(financials: pd.DataFrame | list[dict[str, Any]]) -> dict[str, MetricResult]:
    df = pd.DataFrame(financials)
    if not df.empty:
        for column in df.columns:
            if column != "year":
                df[column] = pd.to_numeric(df[column], errors="coerce")
    return {name: func(df) for name, func in METRIC_FUNCTIONS.items()}
