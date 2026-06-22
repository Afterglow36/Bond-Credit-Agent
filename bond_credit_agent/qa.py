from __future__ import annotations

from pathlib import Path

from bond_credit_agent.prompt_templates import build_rag_prompt
from bond_credit_agent.retriever import LocalEvidenceRetriever
from bond_credit_agent.schemas import EvidenceChunk


def retrieve_question_evidence(
    query: str,
    docs_path: str | Path,
    *,
    template_name: str = "company_fundamentals",
    top_k: int = 4,
) -> tuple[str, list[EvidenceChunk]]:
    """Return an evidence-grounded local RAG answer scaffold without generating new facts."""
    if not query.strip():
        return "Enter a question to retrieve supporting evidence.", []

    retriever = LocalEvidenceRetriever(docs_path)
    chunks = retriever.retrieve(query, top_k=top_k)
    if not chunks:
        return "No local evidence was retrieved. Manual document review is required.", []

    evidence_text = "\n\n".join(
        f"[{chunk.source_file} p.{chunk.page_number or 'N/A'} chunk {chunk.chunk_id}] {chunk.text}"
        for chunk in chunks
    )
    prompt = build_rag_prompt(template_name, query, evidence_text)
    answer = (
        "### Evidence-grounded retrieval result\n\n"
        "This is retrieval output, not an LLM-generated conclusion.\n\n"
        f"**Question:** {query}\n\n"
        "**Retrieved evidence:**\n\n"
        f"{evidence_text}\n\n"
        "<details><summary>Constrained prompt scaffold</summary>\n\n"
        f"```text\n{prompt}\n```\n\n"
        "</details>"
    )
    return answer, chunks
