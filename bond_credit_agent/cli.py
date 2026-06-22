from __future__ import annotations

import argparse
import sys

from bond_credit_agent.exceptions import UserInputError
from bond_credit_agent.workflow import run_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the bond credit due diligence MVP workflow.")
    parser.add_argument("--issuer", required=True, help="Path to issuer profile JSON.")
    parser.add_argument("--financials", required=True, help="Path to financial CSV.")
    parser.add_argument("--docs", required=True, help="Path to local text evidence documents.")
    parser.add_argument("--output", required=True, help="Path for generated markdown report.")
    parser.add_argument(
        "--use-llm-report",
        action="store_true",
        help="Optionally polish the deterministic report with an LLM when OPENAI_API_KEY is set.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        report = run_workflow(
            issuer_path=args.issuer,
            financials_path=args.financials,
            docs_path=args.docs,
            output_path=args.output,
            use_llm_report=args.use_llm_report,
        )
    except UserInputError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(f"Generated credit report for {report.issuer_name}: {args.output}")
    print(f"Risk flags: {len(report.risk_flags)}")


if __name__ == "__main__":
    main()
