from __future__ import annotations

import io
from typing import Iterable, Tuple

import pdfplumber
from docx import Document as DocxDocument


def parse_pdf(data: bytes) -> Tuple[str, int]:
    text_parts: list[str] = []
    num_pages = 0
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        num_pages = len(pdf.pages)
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts).strip(), num_pages


def parse_docx(data: bytes) -> Tuple[str, int]:
    doc = DocxDocument(io.BytesIO(data))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip(), 0


def extract_text(filename: str, data: bytes) -> Tuple[str, int]:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return parse_pdf(data)
    if lower.endswith(".docx"):
        return parse_docx(data)
    raise ValueError("Unsupported file type (only PDF/DOCX)")


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> Iterable[str]:
    # Простой чанкер: режет по предложениям/абзацам, стараясь держать длину <= max_chars.
    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
    current: list[str] = []
    current_len = 0
    for para in paragraphs:
        if current_len + len(para) + 1 <= max_chars:
            current.append(para)
            current_len += len(para) + 1
            continue

        if current:
            yield "\n".join(current)
            tail = "\n".join(current)[-overlap:]
            current = [tail, para]
            current_len = len(tail) + len(para) + 1
        else:
            yield para[:max_chars]
            current = [para[max_chars - overlap :]]
            current_len = len(current[0])

    if current:
        yield "\n".join(current)

