from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, PlainSerializer

Money = Annotated[
    Decimal,
    PlainSerializer(lambda v: f"{v:.2f}", return_type=str, when_used="json"),
]


class HealthResponse(BaseModel):
    status: str


class ParserMetadata(BaseModel):
    name: str
    bank_label: str
    display_name: str
    institution: str
    statement_type: str
    country: str
    supports_password: bool


class Totals(BaseModel):
    debit: Money
    credit: Money
    net: Money


class TransactionOut(BaseModel):
    txn_date: str
    post_date: str
    description: str
    amount: Money
    direction: str
    card_last4: str
    cardholder: str
    source_file: str


class StatementParseResponse(BaseModel):
    parser_name: str
    bank_label: str
    statement_date: str
    period: str
    transaction_count: int
    totals: Totals
    transactions: list[TransactionOut]
    meta: dict[str, str]


class ApiError(BaseModel):
    error: str
    message: str
