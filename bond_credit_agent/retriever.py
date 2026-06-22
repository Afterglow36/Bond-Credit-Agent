from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

from bond_credit_agent.ingestion import parse_documents
from bond_credit_agent.schemas import EvidenceChunk

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # pragma: no cover - fallback is tested by behavior.
    TfidfVectorizer = None
    cosine_similarity = None

try:
    import faiss
except Exception:  # pragma: no cover - optional dependency.
    faiss = None


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


class LocalEvidenceRetriever:
    def __init__(
        self,
        docs_path: str | Path | None = None,
        *,
        chunks: list[EvidenceChunk] | None = None,
        chunk_size_words: int = 120,
    ) -> None:
        self.docs_path = Path(docs_path) if docs_path is not None else None
        self.chunk_size_words = chunk_size_words
        self.chunks: list[EvidenceChunk] = chunks or []
        self.ingestion_warnings: list[str] = []
        self._document_frequency: Counter[str] = Counter()
        self._tfidf_matrix = None
        self._vectorizer = None
        self._faiss_index = None
        self._faiss_vectors = None
        if docs_path is not None and chunks is None:
            self._load()
        self._index()

    def _load(self) -> None:
        if self.docs_path is None:
            return
        if not self.docs_path.exists():
            raise FileNotFoundError(f"Document path not found: {self.docs_path}")
        self.chunks, self.ingestion_warnings = parse_documents(
            self.docs_path,
            chunk_size_words=self.chunk_size_words,
        )

    def _index(self) -> None:
        self._document_frequency.clear()
        for chunk in self.chunks:
            self._document_frequency.update(set(_tokens(chunk.text)))

        if TfidfVectorizer is None or not self.chunks:
            return
        self._vectorizer = TfidfVectorizer(stop_words="english")
        try:
            self._tfidf_matrix = self._vectorizer.fit_transform(chunk.text for chunk in self.chunks)
            self._index_faiss_if_available()
        except ValueError:
            self._vectorizer = None
            self._tfidf_matrix = None

    def _index_faiss_if_available(self) -> None:
        if faiss is None or self._tfidf_matrix is None:
            return
        vectors = self._tfidf_matrix.astype("float32").toarray()
        if vectors.size == 0:
            return
        faiss.normalize_L2(vectors)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        self._faiss_index = index
        self._faiss_vectors = vectors

    def retrieve(self, query: str, top_k: int = 3) -> list[EvidenceChunk]:
        faiss_results = self._faiss_retrieve(query, top_k=top_k)
        if faiss_results:
            return faiss_results
        if self._vectorizer is not None and self._tfidf_matrix is not None and cosine_similarity is not None:
            query_vector = self._vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self._tfidf_matrix).ravel()
            ranked = sorted(enumerate(similarities), key=lambda item: item[1], reverse=True)
            chunks = []
            for index, score in ranked[:top_k]:
                if score <= 0:
                    continue
                chunk = self.chunks[index]
                chunks.append(
                    EvidenceChunk(
                        source_file=chunk.source_file,
                        page_number=chunk.page_number,
                        chunk_id=chunk.chunk_id,
                        text=chunk.text,
                        score=float(score),
                    )
                )
            return chunks
        return self._keyword_retrieve(query, top_k=top_k)

    def _faiss_retrieve(self, query: str, top_k: int = 3) -> list[EvidenceChunk]:
        if self._vectorizer is None or self._faiss_index is None:
            return []
        query_vector = self._vectorizer.transform([query]).astype("float32").toarray()
        if query_vector.size == 0:
            return []
        faiss.normalize_L2(query_vector)
        scores, indices = self._faiss_index.search(query_vector, min(top_k, len(self.chunks)))
        chunks: list[EvidenceChunk] = []
        for score, index in zip(scores[0], indices[0]):
            if index < 0 or score <= 0:
                continue
            chunk = self.chunks[int(index)]
            chunks.append(
                EvidenceChunk(
                    source_file=chunk.source_file,
                    page_number=chunk.page_number,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    score=float(score),
                )
            )
        return chunks

    def _keyword_retrieve(self, query: str, top_k: int = 3) -> list[EvidenceChunk]:
        query_tokens = _tokens(query)
        if not query_tokens or not self.chunks:
            return []
        query_counts = Counter(query_tokens)
        total_chunks = len(self.chunks)
        scored: list[EvidenceChunk] = []
        for chunk in self.chunks:
            chunk_counts = Counter(_tokens(chunk.text))
            score = 0.0
            for token, query_count in query_counts.items():
                if token not in chunk_counts:
                    continue
                idf = math.log((1 + total_chunks) / (1 + self._document_frequency[token])) + 1
                score += query_count * chunk_counts[token] * idf
            if score > 0:
                scored.append(
                    EvidenceChunk(
                        source_file=chunk.source_file,
                        page_number=chunk.page_number,
                        chunk_id=chunk.chunk_id,
                        text=chunk.text,
                        score=score,
                    )
                )
        scored.sort(key=lambda chunk: chunk.score, reverse=True)
        return scored[:top_k]
