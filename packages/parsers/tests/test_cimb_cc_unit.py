"""Unit tests for the CIMB credit card parser.

These tests bypass PDF reading by feeding line-list fixtures directly to
`CIMBCreditCardParser.parse()`. They do not require any private PDF.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

import kasa_parsers  # noqa: F401 — register parsers
from kasa_parsers.cimb_cc.parser import CIMBCreditCardParser
from kasa_parsers.core import Direction, Transaction

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "cimb_cc"

PAGE_SEPARATOR = "--- PAGE ---"


def load_fixture(name: str) -> list[list[str]]:
    """Load a fixture as `pages` (list of pages, each a list of non-empty lines)."""
    text = (FIXTURES / f"{name}.txt").read_text(encoding="utf-8")
    pages: list[list[str]] = []
    current: list[str] = []
    for raw in text.splitlines():
        if raw.strip() == PAGE_SEPARATOR:
            if current:
                pages.append(current)
                current = []
            continue
        if raw.strip():
            current.append(raw)
    if current:
        pages.append(current)
    return pages


def parse(name: str, *, source_name: str = "synthetic.pdf") -> list[Transaction]:
    pages = load_fixture(name)
    statement = CIMBCreditCardParser().parse(pages, Path(source_name))
    return statement.transactions


def parse_full(name: str, *, source_name: str = "synthetic.pdf"):
    pages = load_fixture(name)
    return CIMBCreditCardParser().parse(pages, Path(source_name))


def test_signature_true_for_fixture() -> None:
    pages = load_fixture("single_debit")
    text = "\n".join(ln for page in pages for ln in page)
    assert CIMBCreditCardParser.signature(text) is True


def test_signature_false_for_arbitrary_text() -> None:
    assert CIMBCreditCardParser.signature("hello world") is False
    assert CIMBCreditCardParser.signature("PERINCIAN TAGIHAN only") is False


def test_single_debit() -> None:
    txns = parse("single_debit")
    assert len(txns) == 1
    t = txns[0]
    assert t.direction == Direction.DEBIT
    assert t.amount == 123456.78
    assert t.card_last4 == "9999"
    assert t.cardholder == "JOHN DOE"
    assert t.description == "SOME MERCHANT"
    assert t.txn_date == date(2026, 1, 5)
    assert t.post_date == date(2026, 1, 6)


def test_cr_marker_flips_to_credit() -> None:
    txns = parse("cr_credit")
    assert len(txns) == 1
    assert txns[0].direction == Direction.CREDIT
    assert txns[0].amount == 500_000.00
    assert txns[0].description == "PAYMENT-THANK YOU"


def test_multi_line_description() -> None:
    txns = parse("multi_line_desc")
    assert len(txns) == 2
    assert txns[0].description == "DESCRIPTION LINE 1 DESCRIPTION LINE 2"
    assert txns[0].amount == 12_345.67
    assert txns[1].description == "DESC A DESC B DESC C"
    assert txns[1].amount == 99_999.99


def test_cross_year_post_date() -> None:
    """Statement is Jan 2026; a 28/12 txn must be tagged as Dec 2025."""
    txns = parse("cross_year")
    assert len(txns) == 2

    dec_txn = txns[0]
    assert dec_txn.description == "DECEMBER MERCHANT"
    assert dec_txn.txn_date == date(2025, 12, 28)
    assert dec_txn.post_date == date(2025, 12, 29)

    jan_txn = txns[1]
    assert jan_txn.description == "JANUARY MERCHANT"
    assert jan_txn.txn_date == date(2026, 1, 5)
    assert jan_txn.post_date == date(2026, 1, 6)


def test_stop_token_halts_parsing() -> None:
    """Anything after ENDING BALANCE must be ignored, even if it looks like a txn."""
    txns = parse("stop_token")
    descriptions = [t.description for t in txns]
    assert descriptions == ["BEFORE STOP"]


def test_last_balance_and_subtotal_captured_as_meta() -> None:
    statement = parse_full("balances_meta")
    assert statement.meta == {
        "last_balance_9999": "1,000,000.00",
        "subtotal_9999": "1,010,000.00",
    }
    assert len(statement.transactions) == 1
    assert statement.transactions[0].amount == 10_000.00


def test_multi_card_attribution() -> None:
    """Two cardholders on one statement; txns must be tagged with the correct card."""
    txns = parse("multi_card")
    assert len(txns) == 2
    assert txns[0].card_last4 == "1111"
    assert txns[0].cardholder == "PRIMARY HOLDER"
    assert txns[0].description == "PRIMARY MERCHANT"
    assert txns[1].card_last4 == "2222"
    assert txns[1].cardholder == "SECONDARY HOLDER"
    assert txns[1].description == "SECONDARY MERCHANT"


def test_statement_date_from_filename_wins_over_body() -> None:
    """If filename has _dd-mm-yyyy_ pattern, use it instead of Tgl. Statement line."""
    pages = load_fixture("single_debit")  # body says 15/01/26
    statement = CIMBCreditCardParser().parse(
        pages, Path("anything_19-03-2027_xyz.pdf")
    )
    assert statement.statement_date == date(2027, 3, 19)


def test_statement_date_fallback_to_body() -> None:
    """Without a date in the filename, fall back to Tgl. Statement line."""
    statement = parse_full("single_debit", source_name="no_date_in_name.pdf")
    assert statement.statement_date == date(2026, 1, 15)


def test_missing_statement_date_raises_valueerror() -> None:
    """When neither filename nor body has a statement date, ValueError is raised."""
    pages = [
        [
            "PERINCIAN TAGIHAN",
            "RINGKASAN TAGIHAN",
            "Tgl. Pembukuan",
            "1234 56XX XXXX 9999 JOHN DOE",
            "*** END OF STATEMENT ***",
        ]
    ]
    with pytest.raises(ValueError, match="could not determine statement date"):
        CIMBCreditCardParser().parse(pages, Path("no_date.pdf"))
