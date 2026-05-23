# Kasa Web UI Plan

## Context

Saat ini kode utama Kasa berada di `parsers/` dan masih berbentuk CLI:

```bash
cd parsers
uv run python -m kasa_parsers ../archives/statements/CC-CIMB/
```

CLI sudah bisa:

- Membaca PDF statement.
- Membuka PDF terenkripsi dengan password parser.
- Mendeteksi parser yang cocok.
- Mengekstrak transaksi menjadi model `Statement` dan `Transaction`.
- Menulis hasil ke TSV.
- Melakukan smoke test berbasis rekonsiliasi balance PDF.

Target berikutnya adalah memberi UI berbasis web agar user bisa upload statement, melihat status parsing, melihat hasil transaksi, dan mengunduh data tanpa menjalankan command line.

## Goals

- Membuat web UI lokal/hosted untuk upload PDF statement.
- Memakai parser Python yang sudah ada sebagai source of truth.
- Menampilkan hasil parsing dalam tabel transaksi.
- Menyediakan export TSV/CSV dari hasil parsing.
- Menampilkan error parsing dengan jelas, misalnya password salah atau statement tidak dikenali.
- Menjaga struktur parser tetap modular agar bank baru bisa ditambahkan tanpa mengubah UI besar-besaran.
- Mendesain API dan UI dengan asumsi multi-bank, walaupun implementasi pertama hanya CIMB.

## Non-Goals For First Version

- Belum membangun full accounting system.
- Belum ada multi-user authentication.
- Belum ada AI chat.
- Belum ada dashboard cashflow lengkap.
- Belum ada upload dari email.
- Belum ada cloud object storage.

Hal-hal tersebut bisa ditambahkan setelah web UI parsing dasar stabil.

## Proposed Solution

Gunakan arsitektur web app sederhana dengan Python backend sebagai wrapper atas package parser yang sudah ada.

```text
Browser UI
  -> HTTP API
  -> kasa_parsers Python package
  -> Parsed result
  -> Table/export in browser
```

Rekomendasi awal:

- Backend: FastAPI.
- Frontend: React + Vite.
- Parser core: tetap `parsers/kasa_parsers`.
- Storage awal: filesystem lokal.
- Persistence awal: JSON/SQLite ringan, tergantung kebutuhan history.

Alasan memilih backend Python untuk tahap ini:

- Parser sudah Python dan memakai PyMuPDF.
- Tidak perlu memanggil parser lewat subprocess dari backend TypeScript.
- Error handling bisa memakai exception yang sudah ada: `PdfDecryptError`, `UnknownStatementError`, dan error parser lain.
- Lebih cepat sampai ke web UI pertama.

Alternatif yang masih memungkinkan:

- Bun + Hono sebagai API utama, lalu memanggil parser Python via subprocess.
- Bun + Hono sebagai gateway, Python parser sebagai service terpisah.

Namun untuk MVP internal, Python backend langsung lebih sederhana dan risiko integrasinya lebih rendah.

## Multi-Bank Extensibility

Multi-bank support sebaiknya diperlakukan sebagai bagian dari desain inti, bukan fitur tambahan yang ditempel belakangan. Artinya UI dan API tidak boleh terlalu terikat ke istilah kartu kredit CIMB seperti `card_last4`, `cardholder`, atau nama file `CC-CIMB`.

Prinsip desain:

- Setiap bank/parser tetap menjadi plugin kecil yang mengikuti interface `StatementParser`.
- Parser registry tetap menjadi sumber daftar parser yang tersedia.
- Backend API hanya berinteraksi dengan parser lewat service function umum.
- Frontend menerima metadata parser dari API, bukan hardcode daftar bank.
- Schema transaksi harus punya field umum yang cukup untuk semua bank.
- Field spesifik bank disimpan di `meta` atau `raw`, bukan dipaksa masuk ke semua transaksi.

### Parser Metadata

Tambahkan metadata ke parser agar UI bisa menampilkan pilihan bank dan instruksi yang sesuai.

Contoh:

```python
class CIMBCreditCardParser(StatementParser):
    name = "cimb_cc"
    bank_label = "CC-CIMB"
    display_name = "CIMB Niaga Sharia Credit Card"
    institution = "CIMB Niaga"
    statement_type = "credit_card"
    country = "ID"
    default_password = "210493"
```

Untuk bank baru, parser bisa menambahkan metadata sendiri:

```python
class BCASavingsParser(StatementParser):
    name = "bca_savings"
    bank_label = "BCA"
    display_name = "BCA Savings Account"
    institution = "BCA"
    statement_type = "bank_account"
    country = "ID"
```

### Normalized Statement Model

Model saat ini cukup untuk CIMB credit card, tapi beberapa field terlalu spesifik kartu kredit. Untuk multi-bank, arah yang lebih fleksibel:

```text
Statement
  parser_name
  institution
  account_label
  account_type
  statement_date
  period_start
  period_end
  currency
  transactions[]
  meta

Transaction
  txn_date
  post_date
  description
  amount
  direction
  balance
  currency
  account_ref
  counterparty
  reference
  category
  raw
```

Catatan:

- `balance` penting untuk rekening tabungan/current account, tapi mungkin tidak tersedia di credit card detail.
- `account_ref` bisa berisi last4 kartu, nomor rekening masked, atau label akun.
- `counterparty` dan `reference` bisa kosong jika parser belum bisa ekstrak.
- `raw` menyimpan potongan data sumber untuk debugging dan audit.
- Untuk kompatibilitas awal, `card_last4` dan `cardholder` bisa tetap ada sementara, lalu dipetakan ke `account_ref` dan `meta`.

### Parser Capability

Setiap parser bisa mengekspos capability agar UI tahu apa yang bisa diharapkan.

Contoh API response `GET /api/parsers`:

```json
[
  {
    "name": "cimb_cc",
    "bank_label": "CC-CIMB",
    "display_name": "CIMB Niaga Sharia Credit Card",
    "institution": "CIMB Niaga",
    "statement_type": "credit_card",
    "country": "ID",
    "supports_password": true,
    "supports_balance": false,
    "supports_multiple_accounts": false
  }
]
```

Dengan ini, UI bisa:

- Menampilkan daftar parser/bank yang didukung.
- Memberi hint password jika statement umumnya terenkripsi.
- Tidak menampilkan kolom balance jika parser tidak menghasilkannya.
- Menampilkan label "Card" atau "Account" sesuai statement type.

### Parser Selection UX

Ada dua opsi:

1. Auto-detect parser dari isi PDF.
2. User memilih bank/parser sebelum upload.

Rekomendasi:

- Default: auto-detect.
- Advanced/manual fallback: user bisa memilih bank jika auto-detect gagal.

Alasan:

- Auto-detect membuat UX lebih sederhana.
- Manual fallback membantu saat beberapa parser punya signature yang mirip atau statement baru belum lengkap didukung.

API upload bisa menerima parameter optional:

```text
parser_name=cimb_cc
```

Jika `parser_name` kosong, backend mencoba semua parser via registry. Jika diisi, backend hanya mencoba parser tersebut.

### Adding A New Bank

Workflow ideal untuk menambah bank baru:

1. Buat folder parser baru:

```text
parsers/kasa_parsers/bca/
```

2. Implement class parser:

```python
@register_parser
class BCAParser(StatementParser):
    name = "bca"
    bank_label = "BCA"
    display_name = "BCA Statement"

    @classmethod
    def signature(cls, text: str) -> bool:
        ...

    def parse(self, pages: list[list[str]], source_path: Path) -> Statement:
        ...
```

3. Import package di `kasa_parsers/__init__.py` agar parser terdaftar.
4. Tambahkan sample PDF anonymized/safe fixture jika memungkinkan.
5. Tambahkan test rekonsiliasi atau row-count/golden-file test.
6. UI otomatis melihat parser baru lewat `GET /api/parsers`.

Target desain: menambahkan bank baru tidak memerlukan perubahan frontend, kecuali bank tersebut membutuhkan field/filter khusus.

### Testing Multi-Bank Parsers

Setiap parser bank sebaiknya punya minimal:

- Signature test: parser hanya match statement bank yang benar.
- Parse test: menghasilkan jumlah transaksi yang diharapkan.
- Financial invariant test jika statement menyediakan balance.
- Golden output test untuk beberapa baris penting.
- Unknown statement test agar parser tidak false positive.

Untuk rekening bank biasa, invariant yang bisa dipakai:

```text
ending_balance - starting_balance == sum(CREDIT) - sum(DEBIT)
```

Untuk kartu kredit seperti CIMB saat ini:

```text
ending_balance - last_balance == sum(DEBIT) - sum(CREDIT)
```

## Proposed Repository Structure

```text
kasa/
  parsers/
    kasa_parsers/
      core/
      cimb_cc/
    tests/
    pyproject.toml

  apps/
    api/
      pyproject.toml
      kasa_api/
        main.py
        routes/
        services/
        storage.py

    web/
      package.json
      src/
        App.tsx
        api/
        components/
        pages/

  data/
    uploads/
    parsed/

  docs/
    web-ui-plan.md
```

Notes:

- `parsers/` tetap reusable sebagai library.
- `apps/api/` hanya mengurus HTTP, upload, storage, dan pemanggilan parser.
- `apps/web/` hanya UI.
- `data/` berisi file runtime lokal dan sebaiknya masuk `.gitignore`.

## Backend API Design

### `POST /api/statements/parse`

Upload satu PDF dan parse langsung.

Request:

- `file`: PDF statement.
- `password`: optional override.
- `parser_name`: optional parser override. Jika kosong, backend auto-detect.

Response success:

```json
{
  "statement_id": "2026-04-19_CC-CIMB",
  "parser_name": "cimb_cc",
  "institution": "CIMB Niaga",
  "bank_label": "CC-CIMB",
  "account_type": "credit_card",
  "statement_date": "2026-04-19",
  "period": "2026-04",
  "transaction_count": 24,
  "transactions": [
    {
      "txn_date": "2026-03-18",
      "post_date": "2026-03-20",
      "description": "SAVERS AUSTRALIA PTY ...",
      "amount": 459414.08,
      "direction": "DEBIT",
      "account_ref": "2607",
      "balance": null,
      "currency": "IDR",
      "meta": {
        "cardholder": "WAHYU RISMAWAN"
      }
    }
  ]
}
```

Response error examples:

```json
{
  "error": "PDF_DECRYPT_FAILED",
  "message": "Wrong or missing password."
}
```

```json
{
  "error": "UNKNOWN_STATEMENT",
  "message": "No registered parser matched this statement."
}
```

### `GET /api/statements`

List previously parsed statements.

Useful if we keep local history.

### `GET /api/statements/{id}`

Return parsed statement detail.

### `GET /api/statements/{id}/export.tsv`

Download TSV.

### `GET /api/parsers`

Return supported parsers/banks.

Example:

```json
[
  {
    "name": "cimb_cc",
    "bank_label": "CC-CIMB",
    "display_name": "CIMB Niaga Sharia Credit Card",
    "institution": "CIMB Niaga",
    "statement_type": "credit_card",
    "country": "ID",
    "supports_password": true
  }
]
```

## Frontend UX

First screen should be the working parser UI, not a marketing page.

Core views:

1. Upload view
   - PDF dropzone.
   - Bank/parser selector with "Auto-detect" as default.
   - Optional password field.
   - Parse button.
   - Clear error messages.

2. Parse result view
   - Statement summary: bank, statement date, period, total rows.
   - Totals: debit, credit, net movement.
   - Transaction table.
   - Search/filter by description.
   - Filter by direction.
   - Columns shown based on available fields, for example balance only when provided.
   - Export TSV/CSV button.

3. Statement history view
   - List of parsed statements.
   - Reopen previous result.
   - Delete local result, if persistence is enabled.

Recommended first UI layout:

```text
Top bar: Kasa

Left panel:
  Upload PDF
  Password override
  Supported parser info

Main panel:
  Statement summary
  Totals
  Transaction table
```

## Data Handling

For first version, use local filesystem storage:

```text
data/
  uploads/
    <statement_id>.pdf
  parsed/
    <statement_id>.json
    <statement_id>.tsv
```

If history is not needed yet, the API can parse and return results without storing them permanently.

If history is needed, use SQLite:

```text
statements
  id
  parser_name
  institution
  bank_label
  account_type
  account_ref
  statement_date
  period_start
  period_end
  period
  currency
  source_filename
  created_at

transactions
  id
  statement_id
  txn_date
  post_date
  description
  amount
  direction
  balance
  currency
  account_ref
  counterparty
  reference
  meta_json
```

Recommendation: start with JSON + TSV files. Move to SQLite when dashboard/history queries become important.

## Parser Changes Needed

Minimal parser refactor:

- Add a public function for parsing one PDF and returning a `Statement`.
- Keep CLI behavior unchanged.
- Reuse the same parser selection logic currently in `cli.py`.
- Add parser metadata fields for UI/API discovery.
- Begin migrating card-specific fields toward generic account fields while preserving compatibility.

Suggested new module:

```text
parsers/kasa_parsers/service.py
```

Possible API:

```python
def parse_statement_pdf(
    pdf_path: Path,
    password_override: str | None = None,
    parser_name: str | None = None,
) -> Statement:
    ...
```

Why:

- `cli.py` currently owns orchestration logic.
- Web API should not import private CLI functions like `_process_one`.
- CLI and web API should share one stable parser service function.

## Implementation Phases

### Phase 1: Parser Service Extraction

- Move reusable parse orchestration from `cli.py` into `kasa_parsers/service.py`.
- Keep CLI output behavior the same.
- Add tests for parsing one PDF through the new service function.
- Add parser metadata contract.
- Add optional parser override support.
- Confirm existing smoke test still passes.

Deliverable:

- Parser can be called cleanly from both CLI and future web API.

### Phase 2: API MVP

- Create `apps/api`.
- Add FastAPI app.
- Add upload endpoint: `POST /api/statements/parse`.
- Add parser discovery endpoint: `GET /api/parsers`.
- Map parser exceptions into HTTP errors.
- Return parsed transactions as JSON.
- Add TSV export helper.

Deliverable:

- API can parse a PDF uploaded via HTTP.

### Phase 3: Web UI MVP

- Create `apps/web`.
- Build upload screen.
- Build result table.
- Add loading and error states.
- Add export button.
- Connect to API.

Deliverable:

- User can open browser, upload PDF, see parsed rows, and export.

### Phase 4: Local History

- Decide whether to use JSON files or SQLite.
- Add statement list.
- Add statement detail route.
- Add delete/reparse behavior.

Deliverable:

- Previously parsed statements can be reopened.

### Phase 5: Dashboard Foundation

- Add totals per statement.
- Add monthly debit/credit/net summary.
- Add category field placeholder, even if categorization is manual or rule-based later.
- Ensure queries group by bank/account so future multi-bank data does not get mixed accidentally.

Deliverable:

- The app starts becoming analysis-oriented, not just extraction-oriented.

## Testing Plan

Backend:

- Parser service test against existing CIMB PDFs.
- API upload test with valid PDF.
- API error test for wrong password.
- API error test for unknown statement.

Frontend:

- Upload form renders.
- Valid upload shows transaction table.
- Error response shows user-readable message.
- Export button downloads expected file.

End-to-end:

- Start API and web.
- Upload known CIMB PDF.
- Confirm row count matches existing smoke test.
- Confirm debit/credit/net totals match PDF reconciliation.

## Risks And Tradeoffs

- PDF parsing remains format-sensitive. CIMB statement layout changes can break extraction.
- Different banks expose different fields, so the normalized model must tolerate missing values.
- Some banks may provide running balances, while credit card statements may only provide summary balances.
- Password handling should be treated carefully if this becomes hosted.
- Storing uploaded financial PDFs locally is acceptable for local MVP, but hosted deployment needs encryption, retention policy, and access control.
- TSV is fine for export, but dashboard queries will eventually be easier with SQLite.
- If the final product must use Bun + Hono, Python backend may become a separate parser service later.

## Open Questions

1. Should the first web UI be local-only, or should it be designed for hosted use from day one?
2. Do we need statement history in the first version, or is upload-and-view enough?
3. Should uploaded PDFs be saved, or should only parsed transaction data be retained?
4. Should export be TSV only, or do you want CSV too?
5. Do you prefer the first backend to be Python/FastAPI for speed, or should we follow the earlier product direction of Bun + Hono even if it adds parser integration overhead?
6. Should the UI support multiple PDF upload in the first version?
7. Should the password field default to the parser default password, or stay hidden/empty unless parsing fails?
8. Bank mana yang paling mungkin ditambahkan setelah CIMB: BCA, Mandiri, BNI, atau bank lain?
9. Apakah target statement berikutnya adalah rekening bank biasa, kartu kredit, atau keduanya?
10. Apakah output harus punya schema tunggal lintas bank dari awal, walaupun beberapa field akan kosong?

## Recommended Next Step

Start with Phase 1 and Phase 2:

1. Extract parser orchestration from `cli.py` into `kasa_parsers/service.py`.
2. Add parser metadata and optional parser override.
3. Build a minimal FastAPI endpoint around that service.
4. Verify uploaded CIMB PDFs return the same transaction counts and totals as the current CLI smoke test.

After that, the React UI can be built on top of a stable API contract.
