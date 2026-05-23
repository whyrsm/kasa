from __future__ import annotations

import csv
from pathlib import Path

from .models import Statement

TSV_HEADER = [
    "statement_period",
    "txn_date",
    "post_date",
    "description",
    "amount",
    "direction",
    "card_last4",
    "cardholder",
    "source_file",
]


def write_tsv(statement: Statement, out_path: Path, source_file: str) -> int:
    """Write a Statement to TSV. Returns number of rows written (excl. header)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    period = statement.period
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(TSV_HEADER)
        for t in statement.transactions:
            w.writerow(
                [
                    period,
                    t.txn_date.isoformat(),
                    t.post_date.isoformat(),
                    t.description,
                    f"{t.amount:.2f}",
                    t.direction.value,
                    t.card_last4,
                    t.cardholder,
                    source_file,
                ]
            )
    return len(statement.transactions)
