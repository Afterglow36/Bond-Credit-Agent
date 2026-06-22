from bond_credit_agent.retriever import LocalEvidenceRetriever


def test_retriever_returns_relevant_chunks():
    retriever = LocalEvidenceRetriever("data/sample")

    chunks = retriever.retrieve("liquidity short-term debt refinancing", top_k=2)

    assert chunks
    assert chunks[0].source_file.endswith(".txt")
    assert "liquidity" in chunks[0].text.lower() or "refinancing" in chunks[0].text.lower()


def test_retriever_returns_page_metadata_from_chunks():
    from bond_credit_agent.schemas import EvidenceChunk

    retriever = LocalEvidenceRetriever(
        chunks=[
            EvidenceChunk(source_file="credit.pdf", page_number=7, chunk_id=0, text="Liquidity refinancing debt pressure."),
            EvidenceChunk(source_file="other.txt", chunk_id=1, text="Unrelated operations update."),
        ]
    )

    chunks = retriever.retrieve("liquidity refinancing", top_k=1)

    assert chunks[0].source_file == "credit.pdf"
    assert chunks[0].page_number == 7
