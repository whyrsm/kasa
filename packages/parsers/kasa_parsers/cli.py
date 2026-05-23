from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import PdfDecryptError, UnknownStatementError, write_tsv
from .service import parse_statement_pdf

# Default output: <repo-root>/archives/tsv/, anchored to package location so it
# works regardless of CWD. Package is at <repo-root>/packages/parsers/kasa_parsers/.
DEFAULT_OUT_DIR = Path(__file__).resolve().parents[3] / "archives" / "tsv"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    pdfs = _discover_pdfs(args.input)
    if not pdfs:
        print(f"no PDF files found at {args.input}", file=sys.stderr)
        return 2

    out_dir = args.out or DEFAULT_OUT_DIR
    print(f"Writing TSVs to: {out_dir}")

    ok = 0
    fail = 0
    for pdf in pdfs:
        try:
            out_path, rows = _process_one(
                pdf, password_override=args.password, out_dir=out_dir
            )
        except (PdfDecryptError, UnknownStatementError) as e:
            print(f"FAIL  {pdf.name}: {e}", file=sys.stderr)
            fail += 1
            continue
        except Exception as e:  # noqa: BLE001 — keep batch going
            print(f"FAIL  {pdf.name}: {type(e).__name__}: {e}", file=sys.stderr)
            fail += 1
            continue
        print(f"OK    {pdf.name}  →  {out_path.name}  ({rows} rows)")
        ok += 1

    print(f"\nSummary: OK {ok} / FAIL {fail}")
    return 0 if fail == 0 else 1


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m kasa_parsers",
        description="Extract bank statement PDFs to TSV.",
    )
    p.add_argument("input", type=Path, help="PDF file or directory containing PDFs")
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help=f"Output directory (default: {DEFAULT_OUT_DIR})",
    )
    p.add_argument(
        "--password",
        default=None,
        help="Override PDF password (default: parser-specific default_password)",
    )
    return p.parse_args(argv)


def _discover_pdfs(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() == ".pdf" else []
    if target.is_dir():
        return sorted(p for p in target.rglob("*.pdf"))
    return []


def _process_one(
    pdf: Path,
    *,
    password_override: str | None,
    out_dir: Path,
) -> tuple[Path, int]:
    statement = parse_statement_pdf(pdf, password_override=password_override)

    filename = f"{statement.statement_date.isoformat()}_{statement.bank_label}.tsv"
    out_path = out_dir / filename
    rows = write_tsv(statement, out_path, source_file=pdf.name)
    return out_path, rows
