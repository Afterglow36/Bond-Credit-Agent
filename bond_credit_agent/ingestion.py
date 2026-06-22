from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from bond_credit_agent.chunking import DocumentText, chunk_document_texts
from bond_credit_agent.schemas import EvidenceChunk


SUPPORTED_DOCUMENT_EXTENSIONS = {".txt", ".md", ".pdf", ".csv", ".xlsx"}
IGNORED_SIDECAR_EXTENSIONS = {".json"}


def parse_documents(
    docs_path: str | Path | Iterable[str | Path],
    *,
    chunk_size_words: int = 120,
    overlap_words: int = 20,
) -> tuple[list[EvidenceChunk], list[str]]:
    paths = _resolve_paths(docs_path)
    warnings: list[str] = []
    documents: list[DocumentText] = []

    for path in paths:
        suffix = path.suffix.lower()
        if not path.exists():
            warnings.append(f"Document not found: {path}")
            continue
        if path.stat().st_size == 0:
            warnings.append(f"Skipped empty document: {path.name}")
            continue
        if suffix in IGNORED_SIDECAR_EXTENSIONS:
            continue
        if suffix not in SUPPORTED_DOCUMENT_EXTENSIONS:
            warnings.append(f"Skipped unsupported document type: {path.name}")
            continue
        try:
            documents.extend(_parse_document(path))
        except Exception as exc:
            warnings.append(f"Could not parse {path.name}: {exc}")

    return chunk_document_texts(documents, chunk_size_words=chunk_size_words, overlap_words=overlap_words), warnings


def _resolve_paths(docs_path: str | Path | Iterable[str | Path]) -> list[Path]:
    if isinstance(docs_path, (str, Path)):
        path = Path(docs_path)
        if not path.exists():
            return [path]
        if path.is_dir():
            return sorted(child for child in path.iterdir() if child.is_file())
        return [path]
    return [Path(path) for path in docs_path]


def _parse_document(path: Path) -> list[DocumentText]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return [DocumentText(source_file=path.name, text=path.read_text(encoding="utf-8", errors="replace"))]
    if suffix == ".pdf":
        return _parse_pdf(path)
    if suffix == ".csv":
        df = pd.read_csv(path)
        return [DocumentText(source_file=path.name, text=_dataframe_to_text(df))]
    if suffix == ".xlsx":
        return _parse_xlsx(path)
    return []


def _parse_pdf(path: Path) -> list[DocumentText]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required to parse PDF documents.") from exc

    reader = PdfReader(str(path))
    documents: list[DocumentText] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            text = ""
            documents.append(
                DocumentText(
                    source_file=path.name,
                    page_number=index,
                    text=f"PDF page parsing failed and requires manual review: {exc}",
                )
            )
        if text.strip():
            documents.append(DocumentText(source_file=path.name, page_number=index, text=text))
    return documents


def _parse_xlsx(path: Path) -> list[DocumentText]:
    sheets = pd.read_excel(path, sheet_name=None)
    documents: list[DocumentText] = []
    for sheet_name, df in sheets.items():
        documents.append(DocumentText(source_file=f"{path.name}:{sheet_name}", text=_dataframe_to_text(df)))
    return documents


def _dataframe_to_text(df: pd.DataFrame) -> str:
    cleaned = df.dropna(how="all").fillna("")
    return cleaned.to_csv(index=False)
