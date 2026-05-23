from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import IO

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


def _write_rows(
    statement: Statement,
    source_file: str,
    sink: IO[str],
    delimiter: str = "\t",
) -> int:
    """Write header + rows to `sink`. Returns number of data rows written."""
    period = statement.period
    w = csv.writer(sink, delimiter=delimiter, lineterminator="\n")
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


def write_tsv(statement: Statement, out_path: Path, source_file: str) -> int:
    """Write a Statement to TSV. Returns number of rows written (excl. header)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        return _write_rows(statement, source_file, f)


def statement_to_delimited(
    statement: Statement,
    source_file: str,
    delimiter: str = "\t",
) -> str:
    """Serialize a Statement to a delimited-text string (TSV or CSV)."""
    buf = io.StringIO()
    _write_rows(statement, source_file, buf, delimiter=delimiter)
    return buf.getvalue()
