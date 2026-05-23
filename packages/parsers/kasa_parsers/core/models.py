from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum


class Direction(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


@dataclass(frozen=True)
class Transaction:
    txn_date: date
    post_date: date
    description: str
    amount: Decimal
    direction: Direction
    card_last4: str
    cardholder: str


@dataclass
class Statement:
    parser_name: str
    bank_label: str
    statement_date: date
    transactions: list[Transaction] = field(default_factory=list)
    meta: dict[str, str] = field(default_factory=dict)

    @property
    def period(self) -> str:
        return self.statement_date.strftime("%Y-%m")
