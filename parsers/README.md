# kasa-parsers

Ekstrak PDF bank statement → TSV.

## Setup

```
uv sync
```

## Pakai

Satu file:
```
uv run python -m kasa_parsers ../archives/statements/CC-CIMB/<file>.pdf
```

Satu direktori (rekursif):
```
uv run python -m kasa_parsers ../archives/statements/CC-CIMB/
```

Output: `kasa/archives/tsv/<YYYY-MM-DD>_<BANK-LABEL>.tsv` (mis. `2026-01-19_CC-CIMB.tsv`).
Tanggal = Tgl. Statement (full date dari PDF). Override lokasi pakai `--out DIR`.

Password: tiap parser punya `default_password` sendiri (CIMB: `210493`). Override pakai `--password XXXXX`.

## Bank yang didukung

- CIMB Niaga Sharia Credit Card (`MC GOLD SYARIAH REGULER`)

## Tambah bank baru

1. Buat folder `kasa_parsers/<bank>/`.
2. Implement `StatementParser` — isi `name`, `bank_label`, `default_password`, `signature(text)`, `parse(pages, source_path)`.
3. Decorator `@register_parser` di class.
4. Import package di `kasa_parsers/__init__.py` supaya auto-register.

`bank_label` muncul di nama file output (`<date>_<bank_label>.tsv`).
CLI dan core (PDF reader, TSV writer, registry) tidak perlu diubah.

## Schema TSV

```
statement_period   txn_date   post_date   description   amount   direction   card_last4   cardholder   source_file
```

- `direction`: `DEBIT` / `CREDIT`.
- `amount`: positif, tanpa pemisah ribuan.
- `txn_date`/`post_date`: ISO `YYYY-MM-DD`.
