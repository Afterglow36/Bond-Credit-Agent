from pathlib import Path

from bond_credit_agent.chunking import DocumentText, chunk_document_texts
from bond_credit_agent.ingestion import parse_documents


def test_text_and_markdown_ingestion_preserves_metadata(tmp_path):
    txt = tmp_path / "source.txt"
    md = tmp_path / "memo.md"
    txt.write_text("Liquidity pressure and refinancing risk are rising.", encoding="utf-8")
    md.write_text("Revenue decline creates margin pressure.", encoding="utf-8")

    chunks, warnings = parse_documents(tmp_path, chunk_size_words=10, overlap_words=0)

    assert warnings == []
    assert {chunk.source_file for chunk in chunks} == {"source.txt", "memo.md"}
    assert all(chunk.page_number is None for chunk in chunks)
    assert all(chunk.text for chunk in chunks)


def test_chunking_preserves_page_number():
    chunks = chunk_document_texts(
        [DocumentText(source_file="sample.pdf", page_number=3, text=" ".join(["debt"] * 30))],
        chunk_size_words=10,
        overlap_words=0,
    )

    assert chunks
    assert chunks[0].source_file == "sample.pdf"
    assert chunks[0].page_number == 3
