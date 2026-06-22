from __future__ import annotations

from dataclasses import dataclass

from bond_credit_agent.schemas import EvidenceChunk


@dataclass(frozen=True)
class DocumentText:
    source_file: str
    text: str
    page_number: int | None = None


def chunk_document_texts(
    documents: list[DocumentText],
    *,
    chunk_size_words: int = 120,
    overlap_words: int = 20,
) -> list[EvidenceChunk]:
    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be positive.")
    if overlap_words < 0 or overlap_words >= chunk_size_words:
        raise ValueError("overlap_words must be non-negative and smaller than chunk_size_words.")

    chunks: list[EvidenceChunk] = []
    chunk_id = 0
    step = chunk_size_words - overlap_words
    for document in documents:
        words = document.text.split()
        for start in range(0, len(words), step):
            text = " ".join(words[start : start + chunk_size_words]).strip()
            if not text:
                continue
            chunks.append(
                EvidenceChunk(
                    source_file=document.source_file,
                    page_number=document.page_number,
                    chunk_id=chunk_id,
                    text=text,
                )
            )
            chunk_id += 1
            if start + chunk_size_words >= len(words):
                break
    return chunks
