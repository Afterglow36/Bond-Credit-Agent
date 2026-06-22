# AGENTS.md

Project instructions for future Codex work on `bond-credit-due-diligence-agent`.

- Preserve financial correctness above all else.
- Never fabricate financial numbers, issuer facts, or evidence.
- All financial metrics must be calculated by deterministic Python functions.
- Every risk flag must be grounded in calculated metrics.
- If supporting evidence is missing, mark the relevant item for manual review.
- Keep LLM usage optional in later versions; do not make it required for the core workflow.
- Keep reports evidence-aware, transparent, and human-review-oriented.
- Keep tests passing when changing metric logic, risk rules, retrieval, workflow, or reports.
- Do not add UI features such as Gradio unless explicitly requested in a later round.
