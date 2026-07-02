# Kasa

Kasa turns Indonesian bank statement PDFs into structured transaction data,
locally.

## Why this exists

Most personal finance tools want your banking credentials. You hand them over,
they screen-scrape or talk to an aggregator, and your transaction history ends
up on someone else's server. For Indonesian banks the coverage is also uneven:
sharia products and many credit cards fall outside what consolidators support.

The fallback is opening each monthly PDF and retyping numbers into a
spreadsheet. That works for one statement. It stops working at twelve.

Kasa sits in between. You point it at the PDFs the bank already sends you and
get back rows you can audit, export, and analyze. The PDFs stay on your
machine: no upload to a third party, no OAuth into your bank, no API token
shared with a cloud service.

## What makes it different

- **Local-first.** The parser is a Python library and CLI. The web app is a
  FastAPI service plus a React UI you run yourself. Uploaded PDFs are written
  to a temp file and deleted after the response is prepared.
- **Auditable extraction.** Parser tests reconcile parsed debit/credit
  movement against the opening and closing balances printed on the statement.
  If the math does not match, the test fails. The goal is every row correct,
  not most rows extracted.
- **Bank-aware, not a generic table extractor.** Tools like Tabula or
  `pdfplumber` give you a table. They do not know that `CR` after an amount
  means a credit, that a January statement can contain December transactions,
  or what password format a given bank uses. Each parser in
  `packages/parsers/` encodes those rules.
- **Pluggable.** A new bank is a new package under
  `packages/parsers/kasa_parsers/<bank>/` plus a registry entry. The API and
  UI pick it up automatically.
- **Built for Indonesian statements.** CIMB Niaga Sharia credit card is the
  first supported format. The roadmap is broader coverage, including products
  mainstream consolidators tend to skip.

Today: CLI and a local web UI that handle upload, parse, review, and export
to TSV/CSV for one bank. Planned: more banks, statement history, dashboards,
and a chat assistant grounded in your own transactions.

## Workspace Setup

Install JavaScript dependencies from the repository root:

```bash
npm install
```

Python dependencies are managed by the root `uv` workspace and are synced on
first `uv run`. To install them explicitly:

```bash
uv sync --all-packages
```

## Parser CLI

```bash
uv run --package kasa-parsers python -m kasa_parsers archives/statements/CC-CIMB/
```

Generated TSVs are written under `archives/tsv/`, which is ignored by git.

## Local Web App

Start the API:

```bash
npm run dev:api
```

Start the web UI in a second terminal:

```bash
npm run dev:web
```

The web UI defaults to `http://localhost:8000` for the API. To point it
somewhere else, copy `apps/web/.env.example` to `apps/web/.env` and set
`VITE_API_BASE_URL`.

Uploaded PDFs are stored only in a temporary file during parsing and deleted
after the response is prepared. Do not commit private PDFs or generated exports.

## Verification

Parser smoke test:

```bash
npm run smoke:parsers
```

This smoke test expects local private PDFs under
`archives/statements/CC-CIMB/`.

API tests:

```bash
npm run test:api
```

Web build:

```bash
npm run build:web
```

Default verification:

```bash
npm test
```

## Railway Deployment

Deploy this monorepo as a single Railway service. The build compiles the
React app, then FastAPI serves both the API (under `/api/*`) and the built
frontend (everything else) from one process — one domain, no CORS wiring
between services.

### 1. Create the service

- New Service → Deploy from GitHub repo → this repo.
- Settings → Root Directory: `/`
- Railpack picks up `railpack.json` automatically. It installs Node 22,
  Python 3.12, and `uv` in the same build image (`packages` in
  `railpack.json`), and runs the start command already defined there:

```bash
uv run --package kasa-api uvicorn kasa_api.main:app --app-dir apps/api --host 0.0.0.0 --port ${PORT:-8000}
```

- Settings → Healthcheck Path: `/api/health`
- Settings → Networking → Generate Domain.

### 2. Set the build/install commands and build-time variable

Railpack's default provider only knows one language per build. Since this
build needs both npm and uv, override the install/build commands with
Service Variables (Variables tab, not `railpack.json`):

```bash
RAILPACK_INSTALL_CMD=npm ci && uv sync --all-packages
RAILPACK_BUILD_CMD=npm run build:web
VITE_API_BASE_URL=
```

`VITE_API_BASE_URL` must be set to an empty value. It gets baked into the
JS bundle at build time — leaving it empty makes the frontend call `/api/...`
as a relative path, which resolves correctly against whatever domain Railway
gives the service. `PORT` is injected by Railway automatically — do not set
it manually.

### Notes

- This is a single-page app with no client-side router yet, so
  `StaticFiles(..., html=True)` serving `index.html` only at `/` is enough.
  If client-side routing is added later, the static mount in
  `apps/api/kasa_api/main.py` will need an explicit fallback to `index.html`
  for unmatched paths, or unknown routes will 404 instead of resolving
  client-side.
- Uploaded PDFs are only ever written to a temp file during parsing and
  deleted after the response — no persistent storage/volume is required.
- Prefer two separate services instead? Put the API back on its own
  Railpack config (root `/`, same start command) and the web app on a
  static-site service (root `/apps/web`, build command `npm run build`,
  Railpack auto-serves the Vite `dist` output) with `CORS_ALLOW_ORIGINS` /
  `VITE_API_BASE_URL` cross-referencing each service's
  `RAILWAY_PUBLIC_DOMAIN`. That trades this setup's simplicity for
  independent deploys/scaling of the two halves.
