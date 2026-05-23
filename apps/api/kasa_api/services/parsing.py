from __future__ import annotations

from decimal import Decimal

from kasa_parsers.core import Direction, Statement

from ..schemas import StatementParseResponse, Totals, TransactionOut


def statement_to_response(
    statement: Statement,
    *,
    source_filename: str,
) -> StatementParseResponse:
    debit = sum(
        (t.amount for t in statement.transactions if t.direction == Direction.DEBIT),
        Decimal(0),
    )
    credit = sum(
        (t.amount for t in statement.transactions if t.direction == Direction.CREDIT),
        Decimal(0),
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
