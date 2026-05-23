# User Stories

Dokumen ini adalah living document untuk kebutuhan produk Kasa.

Setiap kali ada improvement aplikasi yang mengubah perilaku user-facing, flow utama, API publik, kemampuan parser, atau cakupan produk, agent harus membaca dan memperbarui file ini sebelum membuat commit.

Jika perubahan teknis tidak berdampak ke user story, tambahkan catatan singkat di bagian "Maintenance Log" bahwa tidak ada user story yang berubah.

## Product Summary

Kasa membantu user mengubah PDF bank statement menjadi data transaksi yang terstruktur, bisa diperiksa, diekspor, dan nantinya dianalisis lewat dashboard atau AI assistant.

Saat ini kemampuan utama masih berpusat pada parser PDF ke TSV. Arah berikutnya adalah UI berbasis web dan dukungan multi-bank.

## Personas

### Small Business Owner

Pemilik bisnis kecil yang ingin memahami cashflow tanpa harus membuka PDF statement satu per satu atau copy-paste ke spreadsheet.

### Operator / Finance Assistant

Orang yang membantu mengumpulkan statement, melakukan parsing, mengecek transaksi, dan mengekspor data untuk akuntan atau analisis internal.

### Developer / Maintainer

Engineer yang menambah parser bank baru, memperbaiki akurasi ekstraksi, dan menjaga agar CLI/API/UI tetap konsisten.

## Current User Stories

### CLI Statement Parsing

- As a user, I want to parse a CIMB Niaga Sharia credit card PDF so that I can get structured transaction data.
- As a user, I want to parse one PDF file or a directory of PDF files so that I can process monthly statements in batch.
- As a user, I want the parser to use the default password for supported statement formats so that I do not need to pass a password every time.
- As a user, I want to override the PDF password so that I can parse statements with a different password.
- As a user, I want parsed output written as TSV so that I can open it in spreadsheet tools.
- As a user, I want each parsed transaction to include dates, description, amount, direction, account/card reference, cardholder metadata, and source file so that the output is auditable.
- As a user, I want clear errors when a PDF cannot be decrypted or the statement format is unknown so that I know what needs fixing.

### Parser Reliability

- As a maintainer, I want parser tests to reconcile parsed debit/credit movement against statement balances so that extraction errors are caught early.
- As a maintainer, I want credit transactions marked correctly when the PDF indicates `CR` so that payments and refunds are not counted as spending.
- As a maintainer, I want transaction dates to handle statement periods that cross calendar years so that December transactions in January statements are dated correctly.

### Privacy And Data Handling

- As a user, I want personal financial PDFs and generated TSVs stored under ignored archive folders so that private data is not committed accidentally.
- As a user, I want generated financial exports ignored by git so that private output files remain local.

## Planned User Stories

### Web Upload

- As a user, I want to open a web UI so that I can parse statements without using the command line.
- As a user, I want to upload a PDF statement from the browser so that the app can parse it.
- As a user, I want to optionally enter a PDF password so that encrypted statements can be processed.
- As a user, I want the app to auto-detect the statement parser so that I do not need to know the internal parser name.
- As a user, I want to manually select a bank/parser when auto-detection fails so that I can retry with a specific format.
- As a user, I want to see upload and parsing progress so that I know the app is working.
- As a user, I want clear, human-readable errors for wrong password, unsupported statement, or parser failure so that I can take corrective action.

### Web Results

- As a user, I want to see a statement summary after parsing so that I can quickly verify bank, period, and transaction count.
- As a user, I want to see debit, credit, and net totals so that I can sanity-check the statement.
- As a user, I want to inspect parsed transactions in a table so that I can review extraction quality.
- As a user, I want to search transaction descriptions so that I can quickly find a merchant or payment.
- As a user, I want to filter transactions by direction so that I can focus on spending or credits.
- As a user, I want table columns to adapt to available data so that bank-specific missing fields do not create confusing empty UI.
- As a user, I want to export parsed data as TSV or CSV so that I can use it outside Kasa.

### Statement History

- As a user, I want to reopen previously parsed statements so that I do not need to upload the same file repeatedly.
- As a user, I want to delete local parsed statements so that I can control stored financial data.
- As a user, I want to choose whether uploaded PDFs are retained or discarded after parsing so that I can balance convenience and privacy.

### Multi-Bank Support

- As a user, I want Kasa to support banks beyond CIMB so that I can consolidate statements from multiple accounts.
- As a user, I want the UI to show supported banks and statement types so that I know what files can be parsed.
- As a maintainer, I want each bank parser to register itself with metadata so that the API and UI can discover supported parsers automatically.
- As a maintainer, I want a normalized transaction schema across banks so that the UI and exports remain consistent.
- As a maintainer, I want bank-specific fields stored in metadata so that adding one bank does not break other parsers.
- As a maintainer, I want parser-specific reliability tests so that new bank support is safe to extend.

### Dashboard Foundation

- As a user, I want monthly income/spending summaries so that I can understand cashflow trends.
- As a user, I want top spending categories so that I can identify major cost drivers.
- As a user, I want unusual transactions highlighted so that I can review anomalies.
- As a user, I want recurring subscriptions detected so that I can audit ongoing expenses.

### AI Financial Chat

- As a user, I want to ask questions about parsed transactions in Bahasa Indonesia or English so that I can get custom financial answers.
- As a user, I want the assistant to answer using parsed transaction data so that responses are grounded in my statements.
- As a user, I want the assistant to show which transactions support an answer so that I can verify the result.

## Acceptance Criteria Guidelines

Every user-facing story should eventually have acceptance criteria that answer:

- What input does the user provide?
- What output or visible behavior should happen?
- What error states should be handled?
- What private data is stored, ignored, or deleted?
- What tests prove the behavior works?

## Maintenance Rules For Agents

Before committing changes, check whether the change affects any of these areas:

- Parser capability or supported bank/statement type.
- CLI usage or output schema.
- API contract.
- Web UI flow.
- Export format.
- Statement storage or privacy behavior.
- Dashboard or analysis behavior.
- AI assistant behavior.

If yes, update the relevant user stories before commit.

If no, add an entry to "Maintenance Log" saying no user story update was required.

## Maintenance Log

- 2026-05-23: Initial user stories document created. Current CLI parser behavior, planned web UI, multi-bank extensibility, privacy handling, dashboard direction, and AI chat direction documented.
