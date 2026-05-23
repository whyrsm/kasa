from __future__ import annotations

from pathlib import Path

import fitz


class PdfDecryptError(Exception):
    pass


def read_pdf_pages(path: Path, password: str | None) -> list[list[str]]:
    """Open a (possibly encrypted) PDF and return its text as pages of lines.

    Returns one inner list per page; each inner list is the page's text split
    on newlines with empty lines dropped.
    """
    with fitz.open(path) as doc:
        if doc.needs_pass:
            if password is None or not doc.authenticate(password):
                raise PdfDecryptError(
                    f"failed to decrypt {path.name}: wrong or missing password"
                )
        return [
            [line for line in page.get_text().splitlines() if line.strip()]
            for page in doc
        ]
