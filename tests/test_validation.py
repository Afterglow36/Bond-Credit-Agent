import json
import subprocess
import sys

import pytest

from bond_credit_agent.exceptions import UserInputError
from bond_credit_agent.financial_metrics import load_financials
from bond_credit_agent.ingestion import parse_documents
from bond_credit_agent.workflow import load_inputs


def test_invalid_financial_input_missing_columns(tmp_path):
    financials = tmp_path / "bad.csv"
    financials.write_text("year,revenue\n2025,100\n", encoding="utf-8")

    with pytest.raises(UserInputError, match="missing required columns"):
        load_financials(financials)


def test_malformed_financial_input_is_user_friendly(tmp_path):
    financials = tmp_path / "bad.xlsx"
    financials.write_text("not an excel file", encoding="utf-8")

    with pytest.raises(UserInputError, match="Could not read financial file"):
        load_financials(financials)


def test_invalid_issuer_json_is_user_friendly(tmp_path):
    issuer = tmp_path / "issuer.json"
    issuer.write_text("{bad json", encoding="utf-8")

    with pytest.raises(UserInputError, match="valid JSON"):
        load_inputs(issuer, "data/sample/financials_sample.csv")


def test_missing_issuer_fields_are_user_friendly(tmp_path):
    issuer = tmp_path / "issuer.json"
    issuer.write_text(json.dumps({"issuer_name": "Incomplete Co"}), encoding="utf-8")

    with pytest.raises(UserInputError, match="missing required fields"):
        load_inputs(issuer, "data/sample/financials_sample.csv")


def test_unsupported_document_format_returns_warning(tmp_path):
    unsupported = tmp_path / "memo.docx"
    unsupported.write_text("unsupported", encoding="utf-8")

    chunks, warnings = parse_documents(tmp_path)

    assert chunks == []
    assert "unsupported document type" in warnings[0]


def test_cli_end_to_end(tmp_path):
    output = tmp_path / "report.md"
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "bond_credit_agent.cli",
            "--issuer",
            "data/sample/issuer_profile_sample.json",
            "--financials",
            "data/sample/financials_sample.csv",
            "--docs",
            "data/sample",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert output.exists()
    assert "Risk flags: 8" in result.stdout
