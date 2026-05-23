from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from ..core import (
    Direction,
    Statement,
    StatementParser,
    Transaction,
    register_parser,
)

CARD_HEADER = re.compile(
    r"^\d{4}\s+\d{2}XX\s+XXXX\s+(?P<last4>\d{4})\s+(?P<name>.+)$"
)
DATE = re.compile(r"^\d{2}/\d{2}$")
AMOUNT = re.compile(r"^[\d,]+\.\d{2}$")
FILENAME_DATE = re.compile(r"_(\d{2})-(\d{2})-(\d{4})_")
STMT_DATE_LINE = re.compile(r"^(\d{2})/(\d{2})/(\d{2})$")

STOP_TOKENS = {"ENDING BALANCE", "*** END OF STATEMENT ***"}


@register_parser
class CIMBCreditCardParser(StatementParser):
    name = "cimb_cc"
    bank_label = "CC-CIMB"
    default_password = "210493"

    SIGNATURE_TOKENS = ("PERINCIAN TAGIHAN", "RINGKASAN TAGIHAN", "Tgl. Pembukuan")

    @classmethod
    def signature(cls, text: str) -> bool:
        return all(tok in text for tok in cls.SIGNATURE_TOKENS)

    def parse(self, pages: list[list[str]], source_path: Path) -> Statement:
        statement_date = _statement_date(pages, source_path)
        stmt_year, stmt_month = statement_date.year, statement_date.month

        lines: list[str] = [ln for page in pages for ln in page]
        transactions: list[Transaction] = []
        meta: dict[str, str] = {}

        card_last4 = ""
        cardholder = ""
        in_block = False
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]

            if line in STOP_TOKENS:
                break

            m = CARD_HEADER.match(line)
            if m:
                card_last4 = m.group("last4")
                cardholder = m.group("name").strip()
                in_block = True
                i += 1
                continue

            if not in_block:
                i += 1
                continue

            if line == "LAST BALANCE":
                if i + 1 < n and AMOUNT.match(lines[i + 1]):
                    meta[f"last_balance_{card_last4}"] = lines[i + 1]
                    i += 2
                else:
                    i += 1
                continue

            if line == "SUBTOTAL":
                if i + 1 < n and AMOUNT.match(lines[i + 1]):
                    meta[f"subtotal_{card_last4}"] = lines[i + 1]
                    i += 2
                else:
                    i += 1
                continue

            if DATE.match(line) and i + 1 < n and DATE.match(lines[i + 1]):
                consumed = _try_consume_transaction(
                    lines,
                    i,
                    stmt_year=stmt_year,
                    stmt_month=stmt_month,
                    card_last4=card_last4,
                    cardholder=cardholder,
                    out=transactions,
                )
                if consumed:
                    i += consumed
                    continue

            i += 1

        return Statement(
            parser_name=self.name,
            bank_label=self.bank_label,
            statement_date=statement_date,
            transactions=transactions,
            meta=meta,
        )


MAX_DESC_LINES = 3
DESC_BAILOUT = {"SUBTOTAL", "LAST BALANCE", "ENDING BALANCE", "*** END OF STATEMENT ***"}


def _try_consume_transaction(
    lines: list[str],
    i: int,
    *,
    stmt_year: int,
    stmt_month: int,
    card_last4: str,
    cardholder: str,
    out: list[Transaction],
) -> int:
    """If lines[i:] starts a transaction block, append it to `out` and return
    the number of lines consumed. Otherwise return 0.

    A transaction is: dd/mm, dd/mm, <desc spanning 1..MAX_DESC_LINES>, amount,
    optional 'CR' marker.
    """
    n = len(lines)
    desc_start = i + 2
    for desc_end in range(desc_start + 1, min(desc_start + 1 + MAX_DESC_LINES, n)):
        candidate = lines[desc_end]
        if not AMOUNT.match(candidate):
            if (
                candidate in DESC_BAILOUT
                or DATE.match(candidate)
                or CARD_HEADER.match(candidate)
            ):
                return 0
            continue
        desc = " ".join(lines[desc_start:desc_end])
        txn = _build_transaction(
            txn_str=lines[i],
            post_str=lines[i + 1],
            desc=desc,
            amount_str=candidate,
            stmt_year=stmt_year,
            stmt_month=stmt_month,
            card_last4=card_last4,
            cardholder=cardholder,
        )
        consumed = desc_end - i + 1
        if desc_end + 1 < n and lines[desc_end + 1] == "CR":
            txn = _flip_to_credit(txn)
            consumed += 1
        out.append(txn)
        return consumed
    return 0


def _statement_date(pages: list[list[str]], source_path: Path) -> date:
    """Return the full statement date.

    Prefer the filename (`..._19-01-2026_...pdf`) since it's unambiguous.
    Fall back to the line after `Tgl. Statement` (format `dd/mm/yy`).
    """
    m = FILENAME_DATE.search(source_path.name)
    if m:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))

    flat = [ln for page in pages for ln in page]
    for idx, ln in enumerate(flat):
        if ln == "Tgl. Statement" and idx + 1 < len(flat):
            sm = STMT_DATE_LINE.match(flat[idx + 1])
            if sm:
                return date(2000 + int(sm.group(3)), int(sm.group(2)), int(sm.group(1)))
    raise ValueError(f"could not determine statement date for {source_path.name}")


def _build_transaction(
    *,
    txn_str: str,
    post_str: str,
    desc: str,
    amount_str: str,
    stmt_year: int,
    stmt_month: int,
    card_last4: str,
    cardholder: str,
) -> Transaction:
    return Transaction(
        txn_date=_parse_date(txn_str, stmt_year, stmt_month),
        post_date=_parse_date(post_str, stmt_year, stmt_month),
        description=desc.strip(),
        amount=_parse_amount(amount_str),
        direction=Direction.DEBIT,
        card_last4=card_last4,
        cardholder=cardholder,
    )


def _flip_to_credit(t: Transaction) -> Transaction:
    return Transaction(
        txn_date=t.txn_date,
        post_date=t.post_date,
        description=t.description,
        amount=t.amount,
        direction=Direction.CREDIT,
        card_last4=t.card_last4,
        cardholder=t.cardholder,
    )


def _parse_date(s: str, stmt_year: int, stmt_month: int) -> date:
    day, month = (int(x) for x in s.split("/"))
    year = stmt_year - 1 if month > stmt_month else stmt_year
    return date(year, month, day)


def _parse_amount(s: str) -> float:
    return float(s.replace(",", ""))
