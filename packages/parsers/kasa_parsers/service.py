from __future__ import annotations

from pathlib import Path

from .core import (
    PdfDecryptError,
    Statement,
    StatementParser,
    UnknownStatementError,
    all_parsers,
    read_pdf_pages,
)


def parse_statement_pdf(
    pdf_path: Path,
    password_override: str | None = None,
    parser_name: str | None = None,
) -> Statement:
    """Parse a PDF statement using auto-detection or an explicit parser."""
    parser_cls, pages = _select_parser_with_pages(
        pdf_path,
        password_override=password_override,
        parser_name=parser_name,
    )
    return parser_cls().parse(pages, pdf_path)


def get_parser_metadata() -> list[dict[str, object]]:
    """Return metadata for parsers that can be shown in UI/API clients."""
    return [
        {
            "name": cls.name,
            "bank_label": cls.bank_label,
            "display_name": _display_name(cls),
            "institution": getattr(cls, "institution", "CIMB Niaga"),
            "statement_type": getattr(cls, "statement_type", "credit_card"),
            "country": getattr(cls, "country", "ID"),
            "supports_password": cls.default_password is not None,
        }
        for cls in all_parsers()
    ]


def _select_parser_with_pages(
    pdf_path: Path,
    *,
    password_override: str | None,
    parser_name: str | None,
) -> tuple[type[StatementParser], list[list[str]]]:
    parsers = all_parsers()
    if not parsers:
        raise UnknownStatementError("no parsers registered")

    if parser_name:
        parser_cls = _parser_by_name(parser_name, parsers)
        password = password_override or parser_cls.default_password
        pages = read_pdf_pages(pdf_path, password)
        text = _pages_text(pages)
        if not parser_cls.signature(text):
            raise UnknownStatementError(f"decrypted but content does not match {parser_cls.name}")
        return parser_cls, pages

    if password_override is not None:
        pages = read_pdf_pages(pdf_path, password_override)
        text = _pages_text(pages)
        for parser_cls in parsers:
            if parser_cls.signature(text):
                return parser_cls, pages
        raise UnknownStatementError(
            f"override password worked but no parser matched content of {pdf_path.name}"
        )

    last_err: Exception | None = None
    for parser_cls in parsers:
        try:
            pages = read_pdf_pages(pdf_path, parser_cls.default_password)
        except PdfDecryptError as e:
            last_err = e
            continue
        text = _pages_text(pages)
        if parser_cls.signature(text):
            return parser_cls, pages
        last_err = UnknownStatementError(
            f"{parser_cls.name} decrypted {pdf_path.name} but content did not match"
        )

    assert last_err is not None
    raise last_err


def _parser_by_name(
    parser_name: str,
    parsers: list[type[StatementParser]],
) -> type[StatementParser]:
    for parser_cls in parsers:
        if parser_cls.name == parser_name:
            return parser_cls
    available = ", ".join(cls.name for cls in parsers)
    raise UnknownStatementError(f"unknown parser {parser_name!r}. Available parsers: {available}")


def _display_name(parser_cls: type[StatementParser]) -> str:
    if hasattr(parser_cls, "display_name"):
        return str(parser_cls.display_name)
    return parser_cls.name.replace("_", " ").title()


def _pages_text(pages: list[list[str]]) -> str:
    return "\n".join(ln for page in pages for ln in page)
