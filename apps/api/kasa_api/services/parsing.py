from __future__ import annotations

from pathlib import Path

from kasa_parsers.core import Direction, Statement
from kasa_parsers.service import parse_statement_pdf

from ..schemas import StatementParseResponse, Totals, TransactionOut


def parse_pdf_to_response(
    pdf_path: Path,
    *,
    source_filename: str,
    password: str | None,
    parser_name: str | None,
) -> StatementParseResponse:
    statement = parse_statement_pdf(
        pdf_path,
        password_override=_none_if_blank(password),
        parser_name=_none_if_blank(parser_name),
    )
    return statement_to_response(statement, source_filename=source_filename)


def statement_to_response(
    statement: Statement,
    *,
    source_filename: str,
) -> StatementParseResponse:
    debit = sum(
        t.amount for t in statement.transactions if t.direction == Direction.DEBIT
    )
    credit = sum(
        t.amount for t in statement.transactions if t.direction == Direction.CREDIT
    )
    transactions = [
        TransactionOut(
            txn_date=t.txn_date.isoformat(),
            post_date=t.post_date.isoformat(),
            description=t.description,
            amount=t.amount,
            direction=t.direction.value,
            card_last4=t.card_last4,
            cardholder=t.cardholder,
            source_file=source_filename,
        )
        for t in statement.transactions
    ]
    return StatementParseResponse(
        parser_name=statement.parser_name,
        bank_label=statement.bank_label,
        statement_date=statement.statement_date.isoformat(),
        period=statement.period,
        transaction_count=len(statement.transactions),
        totals=Totals(debit=debit, credit=credit, net=debit - credit),
        transactions=transactions,
        meta=statement.meta,
    )


def _none_if_blank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
