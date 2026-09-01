# quillink-mcp

An [MCP](https://modelcontextprotocol.io) server exposing **read-only** access to your [Quillink](https://note-taking-app-prod.web.app) notes, folders, and tags to AI tools like Claude Desktop, Claude Code, and other MCP-compatible clients.

Requires a **Pro** Quillink plan (API Access is a Pro-only feature).

Not published to PyPI -- build and run it locally from source.

## Build

```bash
git clone https://github.com/dagistankaradeniz/gcp-note-taking-mcp.git
cd gcp-note-taking-mcp
python3 -m venv .venv
.venv/bin/pip install -e .
```

This installs the `quillink-mcp` command into `.venv/bin/`. Note the full
path to that binary (e.g. `/Users/you/gcp-note-taking-mcp/.venv/bin/quillink-mcp`)
-- MCP clients launch it directly, not through an activated shell, so
they need the absolute path.

## Authenticate

Two options:

**Option A — OAuth device login (recommended for interactive use):**

```bash
.venv/bin/quillink-mcp login
```

Opens a device code + verification URL; approve it in your browser. The token is stored in your OS keyring (or `~/.config/quillink-mcp/credential` as a fallback).

**Option B — Personal Access Token:**

Create one in Quillink under **Settings → Developer → Tokens** (scopes: `notes:read`, `folders:read`, `tags:read`), then set it as an environment variable:

```bash
export QUILLINK_TOKEN=qlk_pat_...
```

`QUILLINK_TOKEN` always takes priority over a stored OAuth login.

## Use with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "quillink": {
      "command": "/absolute/path/to/gcp-note-taking-mcp/.venv/bin/quillink-mcp"
    }
  }
}
```

If using a PAT instead of `login`, pass it as an env var in the config:

```json
{
  "mcpServers": {
    "quillink": {
      "command": "/absolute/path/to/gcp-note-taking-mcp/.venv/bin/quillink-mcp",
      "env": { "QUILLINK_TOKEN": "qlk_pat_..." }
    }
  }
}
```

Restart Claude Desktop after editing the config.

## Use with other MCP clients

Any client that can launch a local stdio MCP server works the same way: point it at the absolute path to `.venv/bin/quillink-mcp` (with `QUILLINK_TOKEN` set, or after running `quillink-mcp login` once so the credential is already stored). This includes Claude Code (`claude mcp add quillink -- /absolute/path/to/.venv/bin/quillink-mcp`) and any OpenAI-compatible agent runtime that supports the MCP stdio transport.

## Tools

All read-only — this server cannot create, edit, or delete anything.

| Tool | Description |
|---|---|
| `list_notes` | List notes, filterable by folder, status, tags, pinned |
| `get_note` | Get a single note by id |
| `search_notes` | Full-text search over title + body |
| `get_note_stats` | Note count, storage used, pinned count |
| `get_note_backlinks` | Notes that link to a given note |
| `get_note_graph` | Local link graph (1 or 2 hops) centered on a note |
| `get_global_note_graph` | Whole-account link graph, paginated (Pro plan) |
| `list_note_recipients` | Who a note has been shared with |
| `list_shared_notes` | Notes shared with you by others |
| `list_folders` | List notebooks/folders |
| `get_folder` | Get a single folder by id |
| `list_tags` | List all tags in use |
| `get_organization` | Your Team-plan organization's name, plan tier, seats, alerts |
| `list_organization_members` | Your organization's members (plain members see only their own entry) |

Vault notes are never accessible here — they're end-to-end encrypted client-side, so no server (including this one) can read them. Organization tools 404 for a caller who isn't on a Team-plan organization.

## Configuration (environment variables)

| Variable | Purpose |
|---|---|
| `QUILLINK_TOKEN` | A Personal Access Token — bypasses OAuth login entirely |
| `QUILLINK_API_BASE` | Override the API base URL (default: production) |
| `QUILLINK_CLIENT_ID` | Override the OAuth client id used by `login` |
| `QUILLINK_WORKSPACE` | Use a named workspace's api-base/client-id/credential instead (see below) |

## Workspaces (multiple environments/accounts)

This server is a single long-running process, launched once per MCP client config entry — there's no per-call "switch workspace" the way the CLI has `--workspace`. To use several environments or accounts, register **one server entry per workspace**, each pinned to a different `QUILLINK_WORKSPACE`:

```bash
# One-time: define the workspaces with the CLI (gcp-note-taking-cli)
quillink workspace add staging --api-base https://staging.example.com
quillink workspace login staging

# Point this server at it
QUILLINK_WORKSPACE=staging .venv/bin/quillink-mcp login
```

Then in your MCP client config, add a second server entry (e.g. `quillink-staging`) alongside your existing one, with `"env": {"QUILLINK_WORKSPACE": "staging"}` — both can be active at once.

Workspace metadata (api_base/client_id, no secrets) lives in `~/.config/quillink/workspaces.json` — the same file `gcp-note-taking-cli`'s `quillink workspace add/use` manages, so a workspace defined once via the CLI is immediately visible here. This server keeps its own separate keyring entry per workspace for the actual token, though, so you still need to `login` (or set `QUILLINK_TOKEN`) once per workspace here too. `QUILLINK_TOKEN`/`QUILLINK_API_BASE`/`QUILLINK_CLIENT_ID` set directly always take precedence over `QUILLINK_WORKSPACE`.

## Running it directly (for testing)

```bash
.venv/bin/quillink-mcp login
.venv/bin/quillink-mcp   # runs the server on stdio -- an MCP client normally launches this for you
```
