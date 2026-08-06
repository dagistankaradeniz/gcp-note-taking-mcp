# quillink-mcp

An [MCP](https://modelcontextprotocol.io) server exposing **read-only** access to your [Quillink](https://note-taking-app-prod.web.app) notes, folders, and tags to AI tools like Claude Desktop, Claude Code, and other MCP-compatible clients.

Requires a **Pro** Quillink plan (API Access is a Pro-only feature).

## Install

```bash
pip install quillink-mcp
```

## Authenticate

Two options:

**Option A — OAuth device login (recommended for interactive use):**

```bash
quillink-mcp login
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
      "command": "quillink-mcp"
    }
  }
}
```

If using a PAT instead of `login`, pass it as an env var in the config:

```json
{
  "mcpServers": {
    "quillink": {
      "command": "quillink-mcp",
      "env": { "QUILLINK_TOKEN": "qlk_pat_..." }
    }
  }
}
```

Restart Claude Desktop after editing the config.

## Use with other MCP clients

Any client that can launch a local stdio MCP server works the same way: point it at the `quillink-mcp` command (with `QUILLINK_TOKEN` set, or after running `quillink-mcp login` once so the credential is already stored). This includes Claude Code (`claude mcp add quillink -- quillink-mcp`) and any OpenAI-compatible agent runtime that supports the MCP stdio transport.

## Tools

All read-only — this server cannot create, edit, or delete anything.

| Tool | Description |
|---|---|
| `list_notes` | List notes, filterable by folder, status, tags, pinned |
| `get_note` | Get a single note by id |
| `search_notes` | Full-text search over title + body |
| `get_note_stats` | Note count, storage used, pinned count |
| `list_note_recipients` | Who a note has been shared with |
| `list_shared_notes` | Notes shared with you by others |
| `list_folders` | List notebooks/folders |
| `get_folder` | Get a single folder by id |
| `list_tags` | List all tags in use |

Vault notes are never accessible here — they're end-to-end encrypted client-side, so no server (including this one) can read them.

## Configuration (environment variables)

| Variable | Purpose |
|---|---|
| `QUILLINK_TOKEN` | A Personal Access Token — bypasses OAuth login entirely |
| `QUILLINK_API_BASE` | Override the API base URL (default: production) |
| `QUILLINK_CLIENT_ID` | Override the OAuth client id used by `login` |

## Local development

```bash
python3 -m venv .venv && .venv/bin/pip install -e .
.venv/bin/quillink-mcp login
.venv/bin/quillink-mcp   # runs the server on stdio
```
