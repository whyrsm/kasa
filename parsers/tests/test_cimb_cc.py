"""Smoke test: parse all CC-CIMB PDFs and reconcile against PDF's own RINGKASAN.

Invariant we rely on:
    ENDING_BALANCE - LAST_BALANCE == sum(DEBIT) - sum(CREDIT)

Both balances are printed in every PDF, so this works for any month without
hand-transcribing summary tables.

Run from kasa/parsers/:
    uv run python tests/test_cimb_cc.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import kasa_parsers  # noqa: F401 — register parsers
from kasa_parsers.cimb_cc.parser import CIMBCreditCardParser
from kasa_parsers.core import (
    Direction,
    UnknownStatementError,
    read_pdf_pages,
    resolve_parser,
)
from kasa_parsers.service import get_parser_metadata, parse_statement_pdf

STATEMENTS_DIR = ROOT.parent / "archives" / "statements" / "CC-CIMB"
PASSWORD = "210493"
TOLERANCE = 0.05


def main() -> int:
    pdfs = sorted(STATEMENTS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"no PDFs in {STATEMENTS_DIR}", file=sys.stderr)
        return 2

    failures = 0
    for pdf in pdfs:
        try:
            failures += _check_one(pdf)
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {pdf.name}: {type(e).__name__}: {e}")
            failures += 1

    failures += _check_unknown_statement_raises()
    failures += _check_service_api()
    failures += _check_jan_known_credits()
    print(f"\n{'OK' if failures == 0 else 'FAILED'} ({failures} failures)")
    return 0 if failures == 0 else 1


def _check_one(pdf: Path) -> int:
    pages = read_pdf_pages(pdf, PASSWORD)
    text = "\n".join(ln for page in pages for ln in page)
    parser_cls = resolve_parser(text)
    assert parser_cls is CIMBCreditCardParser, f"wrong parser picked: {parser_cls}"

    statement = parser_cls().parse(pages, pdf)
    debit = sum(t.amount for t in statement.transactions if t.direction == Direction.DEBIT)
    credit = sum(t.amount for t in statement.transactions if t.direction == Direction.CREDIT)
    movement = debit - credit

    last = _extract_amount_after(text, "LAST BALANCE")
    ending = _extract_amount_after(text, "ENDING BALANCE")
    expected_movement = ending - last

    print(f"\n{pdf.name}")
    print(f"  period={statement.period}  rows={len(statement.transactions)}")
    print(f"  DEBIT={debit:,.2f}  CREDIT={credit:,.2f}  movement={movement:,.2f}")
    print(f"  PDF: LAST={last:,.2f}  ENDING={ending:,.2f}  expected_movement={expected_movement:,.2f}")

    fails = 0
    if abs(movement - expected_movement) > TOLERANCE:
        print(
            f"  RECONCILE FAIL: movement {movement:,.2f} != expected {expected_movement:,.2f}"
        )
        fails += 1

    stmt_year = int(statement.period.split("-")[0])
    stmt_month = int(statement.period.split("-")[1])
    for t in statement.transactions:
        if t.txn_date.month > stmt_month and t.txn_date.year != stmt_year - 1:
            print(f"  cross-year FAIL: {t.txn_date} (stmt {statement.period})")
            fails += 1
        if t.txn_date.month <= stmt_month and t.txn_date.year != stmt_year:
            print(f"  in-year FAIL: {t.txn_date} (stmt {statement.period})")
            fails += 1

    return fails


def _extract_amount_after(text: str, label: str) -> float:
    m = re.search(rf"{re.escape(label)}\s*\n([\d,]+\.\d{{2}})", text)
    if not m:
        raise ValueError(f"could not find {label!r} in PDF text")
    return float(m.group(1).replace(",", ""))


def _check_unknown_statement_raises() -> int:
    try:
        resolve_parser("This is some random text without any tokens.")
    except UnknownStatementError:
        print("\nresolve_parser raises UnknownStatementError on unknown text: OK")
        return 0
    print("\nresolve_parser did NOT raise on unknown text: FAIL")
    return 1


def _check_service_api() -> int:
    pdf = STATEMENTS_DIR / "sharia card billing statement_19-01-2026_546386576.pdf"
    fails = 0

    statement = parse_statement_pdf(pdf, parser_name="cimb_cc")
    if statement.parser_name != "cimb_cc":
        print(f"\nservice parser name FAIL: {statement.parser_name}")
        fails += 1
    if statement.period != "2026-01":
        print(f"\nservice period FAIL: {statement.period}")
        fails += 1
    if len(statement.transactions) != 56:
        print(f"\nservice row count FAIL: {len(statement.transactions)}")
        fails += 1

    metadata = get_parser_metadata()
    cimb = [item for item in metadata if item["name"] == "cimb_cc"]
    if not cimb or cimb[0]["display_name"] != "CIMB Niaga Sharia Credit Card":
        print(f"\nservice metadata FAIL: {metadata}")
        fails += 1

    try:
        parse_statement_pdf(pdf, parser_name="missing_parser")
    except UnknownStatementError:
        pass
    else:
        print("\nservice unknown parser override did NOT raise: FAIL")
        fails += 1

    if fails == 0:
        print("\nservice parse override, metadata, unknown parser checks: OK")
    return fails


def _check_jan_known_credits() -> int:
    """Check that known credits in Jan 2026 are tagged correctly."""
    pdf = STATEMENTS_DIR / "sharia card billing statement_19-01-2026_546386576.pdf"
    pages = read_pdf_pages(pdf, PASSWORD)
    statement = CIMBCreditCardParser().parse(pages, pdf)

    google_one = [t for t in statement.transactions if "Google One" in t.description]
    payments = [t for t in statement.transactions if t.description == "PAYMENT-THANK YOU"]
    fails = 0
    if not google_one or google_one[0].direction != Direction.CREDIT:
        print(f"\nGoogle One credit FAIL: {google_one}")
        fails += 1
    if len(payments) != 2 or any(p.direction != Direction.CREDIT for p in payments):
        print(f"\nPAYMENT-THANK YOU FAIL: {payments}")
        fails += 1
    if fails == 0:
        print("\nKnown CR rows tagged correctly (Google One, PAYMENT-THANK YOU): OK")
    return fails


if __name__ == "__main__":
    raise SystemExit(main())
