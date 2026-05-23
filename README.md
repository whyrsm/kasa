# Kasa

Kasa parses private bank statement PDFs into structured transaction data.

## Parser CLI

```bash
cd parsers
uv run python -m kasa_parsers ../archives/statements/CC-CIMB/
```

Generated TSVs are written under `archives/tsv/`, which is ignored by git.

## Local Web App

Start the API:

```bash
cd apps/api
uv run fastapi dev kasa_api/main.py
```

Start the web UI in a second terminal:

```bash
cd apps/web
npm install
npm run dev
```

The web UI defaults to `http://localhost:8000` for the API. To point it
somewhere else, copy `apps/web/.env.example` to `apps/web/.env` and set
`VITE_API_BASE_URL`.

Uploaded PDFs are stored only in a temporary file during parsing and deleted
after the response is prepared. Do not commit private PDFs or generated exports.

## Verification

Parser smoke test:

```bash
cd parsers
uv run python tests/test_cimb_cc.py
```

API tests:

```bash
cd apps/api
uv run python -m pytest
```

Web build:

```bash
cd apps/web
npm run build
```
