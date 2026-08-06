# AGENTS.md — gcp-note-taking-mcp

Instructions for **any** agentic coding tool (Claude Code, OpenCode, Codex, Cursor, Gemini CLI, …).
This is the **canonical** conventions file for this repo. `CLAUDE.md` imports it. Read it fully and follow it before making changes.

**What this repo is:** the Quillink MCP server — a Python [Model Context Protocol](https://modelcontextprotocol.io) server exposing **read-only** access to notes/folders/tags via the `/v1` API defined in `gcp-note-taking-backend`. Ships as a stdio server, built and run locally from source (not published to PyPI). Contains no server or infra code of its own; it's a client of the API Access layer, same as the CLI and web frontend.

**Source of truth:** Confluence space **GNTA**, "API Access" page (shared auth/rate-limiting/versioning — read this first). If code and docs diverge, stop and flag it rather than guessing.

---

## Stack

- Python **3.11+**, the official [`mcp`](https://pypi.org/project/mcp/) SDK (`mcp.server.mcpserver.MCPServer`, stdio transport), `httpx` for the `/v1` client, `keyring` for credential storage.
- `hatchling` as the build backend (no PyPI publish step — see README's "Not published to PyPI" note).

## Repository layout

```
src/quillink_mcp/
  __main__.py    CLI entrypoint: `login`/`logout` subcommands, or run the server with no args
  server.py       Tool registration (MCPServer) -- one @mcp.tool() per /v1 read endpoint
  client.py       Thin /v1 HTTP client (bearer auth, RFC 7807 error surfacing)
  auth.py         PAT (QUILLINK_TOKEN) + OAuth device-grant login, OS keyring + file fallback
pyproject.toml
README.md         Also the source for the web Developer > MCP page's copy -- keep them in sync
```

## Style

- Format & lint with **ruff**; type-check with **mypy**. Both must pass in CI.
- Full type hints everywhere; mirror `gcp-note-taking-cli`'s Go conventions in spirit (thin entrypoint, logic in dedicated modules).
- `snake_case` for functions/vars/modules.
- Every new tool in `server.py` must be **read-only** — no `POST`/`PUT`/`DELETE` calls to `/v1`. If a write tool is ever wanted, that's a deliberate, separately-scoped decision (see README's "no write tools" note), not an incremental addition.

## Domain conventions (must stay consistent)

- All `/v1` requests carry a bearer credential (PAT or OAuth device-grant token) — never a Firebase ID token. See `gcp-note-taking-backend` AGENTS.md for how these are verified server-side.
- `/v1` errors are RFC 7807 Problem Details (`{"detail": ...}` at minimum) — `client.py`'s `_request` extracts `detail` for tool-call error messages; keep that path working if you touch error handling.
- Keep `client.py` in lockstep with `gcp-note-taking-backend`'s `app/routers/v1_*.py` — if a `/v1` endpoint's shape changes, update the corresponding tool in `server.py` in the same change.
- `README.md` is mirrored (not imported) into `gcp-note-taking-frontend`'s `src/components/settings/McpDocsSection.tsx` Developer page tab — update both when install/auth/config instructions change.

## CI gates

- `ruff check .`, `ruff format --check .`, `mypy src` all pass.
- No automated test suite right now (intentional — do not add one until asked; this mirrors the backend's own "no test suite" convention). Verify changes by running a real stdio MCP client round-trip locally (see README's "Running it directly" section) before committing.

## Before you open a PR

- `ruff check . && ruff format --check . && mypy src` all pass.
- If you touched `server.py`'s tool set, update the tool reference table in `README.md` and in `McpDocsSection.tsx` (frontend repo) to match.

---

## Branching Strategy (identical in spirit to infra, backend, frontend, android, ios & cli)

`main` is always in a working state. Never push work-in-progress to `main`.

### Branches
- Always branch from the latest `main`.
- One short-lived branch per unit of work, named `type/short-kebab-slug`:
  - `feat/…` new feature · `fix/…` bug fix · `chore/…` tooling/deps/config
  - `docs/…` docs only · `refactor/…` behavior-preserving · `test/…` tests only · `ci/…` pipeline · `perf/…` performance

### Commits — Conventional Commits
- Format: `type(optional-scope): summary` — imperative, ≤ 72-char summary.
- Types: `feat, fix, chore, docs, refactor, test, ci, perf, build`.
- One logical change per commit; don't mix unrelated work.

### Pull Requests
- Open a PR into `main`; keep it focused and reviewable.
- **CI must be green before merge.** Never merge red CI.
- Prefer **squash merge**; the squash title follows Conventional Commits.

### Never commit
Secrets, `.env`, OAuth client secrets, API tokens, real credential-store contents (`.venv/`, any exported keyring/credential file).
