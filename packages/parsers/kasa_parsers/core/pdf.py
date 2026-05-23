from __future__ import annotations

from pathlib import Path

import fitz


class PdfDecryptError(Exception):
    pass


class InvalidPdfError(Exception):
    """Raised when the input file cannot be opened as a PDF."""


def read_pdf_pages(path: Path, password: str | None) -> list[list[str]]:
    """Open a (possibly encrypted) PDF and return its text as pages of lines.

    Returns one inner list per page; each inner list is the page's text split
    on newlines with empty lines dropped.
    """
    try:
        doc = fitz.open(path)
    except Exception as e:
        raise InvalidPdfError(f"not a valid PDF: {path.name}") from e

    try:
        if doc.needs_pass:
            if password is None or not doc.authenticate(password):
                raise PdfDecryptError(
                    f"failed to decrypt {path.name}: wrong or missing password"
                )
        return [
            [line for line in page.get_text().splitlines() if line.strip()]
            for page in doc
        ]
    finally:
        doc.close()
