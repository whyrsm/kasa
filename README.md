# Kasa

Kasa parses private bank statement PDFs into structured transaction data.

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
