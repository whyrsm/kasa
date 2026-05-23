# AGENT.md

Guidance for AI coding agents working in this repository. Human contributors should read `README.md` first.

## What this repo is

Kasa parses private Indonesian bank statement PDFs into structured transaction data and exposes the result through a small local web app.

## Layout

Monorepo, two package managers side-by-side:

- `apps/api/` — FastAPI service (`kasa-api`), Python. Mounts the parsers package, exposes `/api/health`, `/api/parsers`, `/api/statements`.
- `apps/web/` — React + Vite + TypeScript SPA (`kasa-web`). Talks to the API over HTTP; base URL via `VITE_API_BASE_URL`.
- `packages/parsers/` — `kasa-parsers`, pure-Python parsing library built on `pymupdf`. Has a CLI (`python -m kasa_parsers`) and a service entry point used by the API.
- `archives/` — local-only inputs/outputs. **Gitignored.** Never commit anything under `archives/statements/`, `archives/tsv/`, `archives/analysis/`, or `archives/reimburse/`.
- `docs/` — internal planning docs (`USER_STORIES.md`, `web-ui-plan.md`).
- `railpack.json` — Railway start config for the API service.

Python deps are a uv workspace (root `pyproject.toml` → `apps/api`, `packages/parsers`). JS deps are an npm workspace (root `package.json` → `apps/web`).

## Common commands

Run from repo root unless noted.

| Task | Command |
| --- | --- |
| Install JS deps | `npm install` |
| Install Python deps | `uv sync --all-packages` |
| Dev API | `npm run dev:api` (FastAPI on `:8000`) |
| Dev web | `npm run dev:web` (Vite on `:5173`) |
| Parser CLI | `uv run --package kasa-parsers python -m kasa_parsers <pdf-dir>` |
| API tests | `npm run test:api` |
| Parser smoke test | `npm run smoke:parsers` (needs local PDFs in `archives/statements/CC-CIMB/`) |
| Web build | `npm run build:web` |
| Default verify | `npm test` (runs `test:api` + `build:web`) |

There is no Python linter/formatter wired up. If you add one, surface it in `npm test`.

## Stack boundaries

Respect the split — do not blur these without explicit reason:

- **Python** owns parsing, PDF/OCR work, transaction extraction, anything CPU/data-heavy. Ecosystem is the reason (`pymupdf`, future `pdfplumber`/`pandas`).
- **React/Vite (TS)** owns the user-facing UI only. No parsing or PDF handling in the browser.
- **FastAPI** is the seam. The web app must not import parser code directly; it goes through HTTP.

Adding a new bank parser: drop a new package under `packages/parsers/kasa_parsers/<bank>/` and register it in `kasa_parsers/core/registry.py`. The API picks it up automatically via `import kasa_parsers` in `apps/api/kasa_api/main.py`.

## Privacy

This repo handles real personal financial data.

- Never commit PDFs, TSVs, or any derived export. The `.gitignore` covers the known paths; do not add new directories that bypass it.
- Uploaded PDFs in the API are written to a temp file and deleted after the response — preserve that lifecycle if you touch `apps/api/kasa_api/services/parsing.py` or the statements route.
- Do not paste real statement contents into commit messages, PR descriptions, issues, or chat transcripts.

## Conventions

- Python: 3.11+, type hints, `from __future__ import annotations` at the top of new modules (matches existing style).
- TS: strict mode (`tsconfig.json`), React 18 function components, `lucide-react` for icons.
- Error responses from the API use `{ "error": <code>, "message": <text> }` — see the exception handler in `apps/api/kasa_api/main.py`. Match this shape when adding new endpoints.
- CORS origins come from `CORS_ALLOW_ORIGINS` (comma-separated) and default to localhost Vite ports.

## Deployment

Railway, two services from this same repo:

- API: root `/`, uses `railpack.json` start command, healthcheck `/api/health`.
- Web: root `/apps/web`, build `npm run build`, needs `VITE_API_BASE_URL` pointing at the API service.

CI/CD is Railway-driven; there is no GitHub Actions pipeline yet. If you add one, run `npm test` at minimum.

## What to ask before changing

- Anything that touches the parser output schema (`packages/parsers/kasa_parsers/core/models.py` and the TSV writer) — downstream consumers depend on column order.
- Anything that changes the API contract on `/api/parsers` or `/api/statements` — the web app is the only client today but the shape is the public surface.
- Adding a new top-level directory or a third package manager.
