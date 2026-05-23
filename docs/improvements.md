# Kasa — Improvement Plan

Draft, untuk direview sebelum eksekusi. Setiap item dibuat self-contained supaya bisa dikerjakan terpisah atau di-skip.

Urutan = prioritas saya (impact dibagi effort). Bukan urutan eksekusi wajib.

---

## 1. Migrasi `amount` ke `Decimal`

**Masalah.** Semua nominal disimpan sebagai `float`:

- `packages/parsers/kasa_parsers/core/models.py:18` — `Transaction.amount: float`
- `packages/parsers/kasa_parsers/cimb_cc/parser.py:227` — `_parse_amount` return `float`
- `apps/api/kasa_api/schemas.py:22-23, 30` — `Totals` dan `TransactionOut.amount` `float`
- `apps/api/kasa_api/services/parsing.py:31-36` — `sum(...)` untuk debit/credit, juga float

Untuk satu statement (~50 transaksi rupiah, 6-7 digit) error akumulasinya masih kecil, tapi reconcile test (`packages/parsers/tests/test_cimb_cc.py:80`) sudah memakai `TOLERANCE = 0.05` — itu indikator drift mulai terlihat. Begitu kita tambah agregasi multi-statement atau konversi rate, ini pecah.

**Pendekatan.**

1. Ganti `Transaction.amount` ke `decimal.Decimal`. `_parse_amount` jadi `Decimal(s.replace(",", ""))`.
2. `Statement` tetap dataclass; tidak ada implication serialisasi karena yang nulis JSON adalah pydantic schema.
3. Di `schemas.py`, pakai `Decimal` juga (pydantic v2 native support, default-nya serialize ke string supaya tidak ada precision loss di JSON). Kalau frontend butuh number, sebutkan eksplisit lewat field serializer ke string, lalu di TS pakai string + format saat display.
4. `core/tsv.py` perlu format `Decimal` dengan dua desimal saat tulis.
5. Smoke test `TOLERANCE` bisa diturunkan ke `Decimal("0.00")` setelah migrasi.

**Risiko.** Frontend sekarang `transaction.amount.toFixed(2)` (App.tsx:108) — kalau API balikin string, perlu `Number(amount).toFixed(2)` atau parse lebih awal. Pilihan desain: server return string ("12345.00"), client parse saat butuh aritmatika (filter/sort). Ini sebenarnya lebih bersih — tapi sebut eksplisit di review.

**Verifikasi.** `npm test` + `npm run smoke:parsers` (reconcile harus exact, bukan tolerance).

---

## 2. Bedakan user error vs bug parser di error handler

**Masalah.** `apps/api/kasa_api/routes/statements.py:64-69` menangkap `Exception` generik dan mengubahnya jadi `400 PARSE_FAILED`. Implikasi:

- Bug di parser (KeyError, IndexError, AttributeError) muncul ke user sebagai "PDF kamu tidak bisa di-parse" — padahal yang salah adalah kode kita.
- Tidak ada stack trace di response, dan tidak ada logging — jadi praktis mustahil debug dari log produksi.
- Monitoring tool akan melihat 100% sukses (semua 400 dianggap "valid user error rate") meski parser pecah.

**Pendekatan.**

1. Hapus blok `except Exception`. Biarkan unexpected exception naik jadi 500.
2. Tambah middleware atau exception handler global yang log exception dengan request id, lalu return `{"error": "INTERNAL", "message": "Internal error"}` 500 — jangan bocorkan stack ke user.
3. `ValueError` saat ini sudah ditangkap (statements.py:58). Periksa apakah parser pernah raise `ValueError` untuk hal yang sebenarnya bug (mis. format date tidak dikenal) — kalau iya, pisahkan jadi exception class sendiri (`ParseError`) supaya semantik "user kasih file yang tidak terduga" terpisah dari "logika kita gagal".
4. Tambah structured logging (stdlib `logging` cukup, format JSON kalau mau, atau biarkan plain — Railway capture stdout).

**Risiko.** Beberapa edge case yang sebelumnya jadi 400 silent sekarang jadi 500 noisy. Itu memang yang kita mau — tapi pastikan smoke test catch dulu yang gampang.

**Verifikasi.** Test baru: kirim PDF yang trigger KeyError dari parser dummy → expect 500, bukan 400. Test existing tetap hijau.

---

## 3. Unit test parser tanpa PDF privat

**Masalah.** `apps/api/tests/test_api.py` cuma test boundary HTTP. Test parser sebenarnya (`packages/parsers/tests/test_cimb_cc.py`) butuh PDF privat di `archives/statements/CC-CIMB/`, jadi tidak jalan di CI dan tidak jalan di mesin orang lain. Yang lebih penting: state machine di `cimb_cc/parser.py:42-112` (CR flip, multi-line description, cross-year date, STOP token, LAST_BALANCE/SUBTOTAL meta) sama sekali tidak ditest secara unit.

**Pendekatan.**

`CIMBCreditCardParser.parse(pages, source_path)` sudah menerima `list[list[str]]` — artinya kita bisa bypass PDF reading sepenuhnya.

1. Buat `packages/parsers/tests/fixtures/cimb_cc/` berisi file `.txt`, satu file = satu page, line per baris. Anonimkan: ganti nama kardholder ke `JOHN DOE`, ganti last4 ke `9999`, ganti deskripsi merchant yang sensitif.
2. Loader helper: `load_fixture(name) -> list[list[str]]` yang baca file `.txt` per-page (pisahkan via marker `--- PAGE ---`).
3. Test case minimum:
   - Single transaction debit
   - Single transaction dengan `CR` marker (harus jadi CREDIT)
   - Multi-line description (2 dan 3 baris)
   - Cross-year date (statement Januari, post-date Desember tahun sebelumnya)
   - STOP token (`*** END OF STATEMENT ***`) — transaksi setelahnya tidak boleh ke-parse
   - LAST_BALANCE / SUBTOTAL → masuk ke `meta`
   - `signature()` true untuk fixture, false untuk teks asal
4. Tambah ke `pyproject.toml` parsers package: `pytest` di dev deps, dan script `npm run test:parsers` di root yang panggil `pytest packages/parsers/tests/` (skip yang butuh PDF privat dengan marker).

**Risiko.** Effort terbesar di antara semua item — bikin fixture line-list yang representatif butuh waktu. Tapi sekali ada, refactor parser jadi aman.

**Verifikasi.** `npm run test:parsers` hijau tanpa file di `archives/`.

---

## 4. Test cross-year date logic

**Masalah.** `cimb_cc/parser.py:220-223`:

```python
def _parse_date(s: str, stmt_year: int, stmt_month: int) -> date:
    day, month = (int(x) for x in s.split("/"))
    year = stmt_year - 1 if month > stmt_month else stmt_year
    return date(year, month, day)
```

Aturan: kalau bulan transaksi > bulan statement, anggap tahun sebelumnya. Benar untuk kasus umum kartu kredit (billing cycle yang menyeberang akhir tahun), tapi:

- Tidak ada test sama sekali.
- Edge case: statement Januari 2026 dengan transaksi `15/01` (same month) → `year = 2026`. OK.
- Edge case: statement Januari 2026 dengan post-date `28/12` → `year = 2025`. OK.
- Edge case yang mungkin salah: statement Desember 2025 dengan transaksi `02/12` (awal bulan, same month) → `year = 2025`. OK.
- Edge case yang *pasti salah*: statement Januari 2026 dengan post-date `01/01/2026` yang muncul dengan transaksi date `30/12/2025` — kedua tanggal kita parse independen, tidak ada cross-check antara txn_date dan post_date.

**Pendekatan.** Tergabung dengan item #3 — tambah test case parametrik di fixture parser. Tidak perlu refactor logic kecuali fixture menunjukkan ada kasus yang gagal.

**Verifikasi.** Sub-test dari item #3.

---

## 5. Konsolidasi TSV column order

**Masalah.** Definisi kolom TSV ada di dua tempat:

- `packages/parsers/kasa_parsers/core/tsv.py` — versi server (CLI output).
- `apps/web/src/App.tsx:91-114` — versi client (export button). Berbeda: ada `statement_period` di kolom pertama, sisanya sama tapi urutan harus dijaga manual.

Sekarang konsumen TSV cuma kita sendiri, jadi belum jadi bug. Tapi sekali user mulai integrate ke spreadsheet/budgeting tool, schema drift = data berantakan.

**Pendekatan.** Pilih satu:

**Opsi A — server jadi sumber kebenaran.** Tambah endpoint `POST /api/statements/export?format=tsv|csv` yang terima file + return `text/tab-separated-values`. Client cuma trigger download response. Hapus logic CSV/TSV generation dari `App.tsx`. Pro: satu jalur, browser download otomatis benar. Con: dua roundtrip (parse + export) atau perlu cache server-side (jangan — itu state).

**Opsi B — client cache parse result, server expose schema.** API tambah field `columns: string[]` di response, client iterate dinamis. Pro: tetap satu roundtrip. Con: client tetap punya formatting logic, escape-cell logic, dsb.

**Opsi C — gabungan.** Parse return JSON (sekarang). Export client-side, tapi import kolom list dari shared TS type yang di-generate dari pydantic schema (mis. via `datamodel-code-generator` atau manual sync). Over-engineering untuk size proyek sekarang.

Saya rekomendasi Opsi A. Sederhana, satu sumber kebenaran, dan menghapus 30 baris dari `App.tsx` yang murni concern data engineering.

**Risiko.** User saat ini bisa filter dulu (search + direction) baru export hasil filter. Opsi A perlu kirim filter ke server, atau export semua transaksi (lebih jujur — "export" artinya raw data, filter cuma untuk view). Saya prefer yang kedua.

**Verifikasi.** Manual: parse → klik export → buka di Numbers/Excel, kolom benar.

---

## 6. Batas ukuran upload

**Masalah.** `apps/api/kasa_api/routes/statements.py:36-38` copy `UploadFile.file` ke temp tanpa cek ukuran. PDF 500MB dari user iseng = disk Railway penuh sampai container restart.

**Pendekatan.**

1. Konstanta `MAX_UPLOAD_BYTES = 20 * 1024 * 1024` (20MB — statement CIMB ~500KB, kasih buffer 40x).
2. Sebelum copy: cek `Content-Length` header kalau ada. Reject 413 kalau melebihi.
3. Saat copy, hitung byte yang ditulis. Kalau lewat batas mid-stream, hapus temp file, raise 413.
4. Error code: `FILE_TOO_LARGE`.

**Risiko.** Tidak ada. Batasnya generous.

**Verifikasi.** Test kirim file > 20MB → expect 413.

---

## 7. CLI default path lebih robust

**Masalah.** `packages/parsers/kasa_parsers/cli.py:12`:

```python
DEFAULT_OUT_DIR = Path(__file__).resolve().parents[3] / "archives" / "tsv"
```

Asumsi: package selalu di `<repo>/packages/parsers/kasa_parsers/`. Kalau di-install via wheel ke `~/.local/lib/python3.11/site-packages/`, `parents[3]` jadi `~/.local`, dan TSV nulis ke `~/.local/archives/tsv/`. Silent failure.

**Pendekatan.** Hapus auto-detect. Wajibkan salah satu:

- `--out PATH` argument.
- Env var `KASA_OUT_DIR`.
- Default ke `./archives/tsv/` relatif ke CWD (bukan `__file__`), dengan log eksplisit di-mana ia nulis.

Saya prefer opsi terakhir untuk DX (CLI dari repo root tetap "just works"), tapi tetap eksplisit di output: `"Writing TSVs to: <abs path>"`.

**Risiko.** Behaviour berubah untuk user yang `cd` ke direktori lain dan run CLI tanpa `--out`. Itu user yang minim sekarang (mungkin cuma kita).

**Verifikasi.** Manual: run CLI dari berbagai CWD, output path masuk akal.

---

## 8. Tooling: lint + format

**Masalah.** Tidak ada ruff/black untuk Python, tidak ada ESLint untuk TS. Konsistensi dijaga manual.

**Pendekatan.** Pasang `ruff` saja (lint + format dalam satu tool, fast). Untuk TS, TypeScript strict mode sudah jalan; ESLint optional — saya skip kecuali kamu mau.

1. Root `pyproject.toml`: tambah `[tool.ruff]` config dengan `line-length = 100`, `target-version = "py311"`, `select = ["E", "F", "I", "B", "UP"]`.
2. Tambah `npm run lint` yang panggil `uv run ruff check .` + `uv run ruff format --check .`.
3. Tambah ke `npm test`.

**Risiko.** First run akan kasih banyak lint warning. Strategi: enable rule kecil-kecil dulu (E, F, I), tambah B dan UP setelah baseline bersih.

**Verifikasi.** `npm run lint` hijau.

---

## Rekomendasi urutan

Kalau saya yang pilih:

1. **#2 (error handler)** dulu — quick win, 1-2 jam, langsung memperbaiki observability.
2. **#3 (parser unit test)** — fondasi untuk semua refactor berikutnya. Effort terbesar tapi sekali jadi, aman.
3. **#1 (Decimal)** — setelah #3, jadi punya safety net.
4. **#6 (upload limit)** dan **#7 (CLI path)** — kecil, bisa di-batch.
5. **#5 (TSV konsolidasi)** — setelah #1 supaya tidak refactor dua kali.
6. **#8 (tooling)** — kapan saja, tidak block apa-apa.

#4 (cross-year test) ikut #3, bukan ticket terpisah.

---

## Yang sengaja tidak masuk plan

- **React state pakai useReducer/Zustand** — App.tsx 7 useState. Masih readable. Tunggu sampai ada feature kedua.
- **CI pipeline (GitHub Actions)** — Railway-driven sekarang. Tambah kalau kontributor > 1.
- **Database / persistence** — di luar scope, butuh diskusi arsitektur sendiri.
- **OCR untuk scanned PDF** — out of scope, parser current full-text PDF only.
- **Multi-bank parser** — registry sudah siap, tinggal tambah package. Bukan improvement, itu feature work.
