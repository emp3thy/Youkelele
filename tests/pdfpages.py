"""Count the pages of a PDF in tests (pypdf is a dev dependency only)."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


def count_pages(pdf_bytes: bytes) -> int:
    return len(PdfReader(BytesIO(pdf_bytes)).pages)
