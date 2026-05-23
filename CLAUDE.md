# CLAUDE.md

This file is the entry point for Claude Code in this repository.

See [AGENT.md](./AGENT.md) for the full agent guide — layout, commands, stack boundaries, privacy rules, conventions, and deployment notes. Everything there applies to Claude as well.

## Claude-specific notes

- Default verification before reporting a task done: `npm test` (runs API tests + web build). For parser-only changes, also run `npm run smoke:parsers` if local PDFs are available; if not, say so explicitly rather than skipping silently.
- When the user writes in Bahasa Indonesia, reply in Bahasa Indonesia. Use `saya` / `kamu`; avoid `aku` and Jakarta-gaul registers (`lo`/`gue`).
- Do not append `Co-Authored-By: Claude` or "Generated with Claude Code" footers to commits or PR bodies in this repo.
- Treat `archives/` as off-limits for reads in agent transcripts unless the user explicitly points you at a file there — the contents are real personal financial data.
