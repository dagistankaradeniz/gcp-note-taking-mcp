"""The Quillink MCP server: read-only tools over notes, folders, tags, and
search. Deliberately no write tools in this first release (create/update/
trash notes or folders) -- keeps an AI agent from being able to modify or
delete a user's notes; see the Developer > MCP page for the plan to add a
write-scoped opt-in server later.

Vault notes are never reachable here: the /v1 API itself excludes them
(they're end-to-end encrypted client-side, so the server can't decrypt
them even if it wanted to)."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from .client import QuillinkClient

mcp = MCPServer("quillink")

_client: QuillinkClient | None = None


def _get_client() -> QuillinkClient:
    """Lazy singleton: login (including an interactive device-flow prompt
    on first use) only happens on the first actual tool call, not when the
    MCP client merely lists available tools."""
    global _client
    if _client is None:
        _client = QuillinkClient()
    return _client


@mcp.tool()
def list_notes(
    folder_id: str | None = None,
    status: str = "active",
    tags: list[str] | None = None,
    pinned: bool | None = None,
    limit: int = 50,
    start_after: str | None = None,
) -> dict[str, Any]:
    """List the caller's notes. folder_id="" lists notes with no folder;
    omit it to list across all folders. status is "active" or "trashed".
    Locked notes are included but their body is withheld (null)."""
    return _get_client().get(
        "/notes",
        {
            "folder_id": folder_id,
            "status": status,
            "tags": tags,
            "pinned": pinned,
            "limit": limit,
            "start_after": start_after,
        },
    )


@mcp.tool()
def get_note(note_id: str) -> dict[str, Any]:
    """Get a single note by id. Fails with 403 if it isn't owned by the
    caller, 404 if it doesn't exist."""
    return _get_client().get(f"/notes/{note_id}")


@mcp.tool()
def search_notes(q: str, limit: int = 50) -> dict[str, Any]:
    """Full-text search over the caller's active notes' titles and body
    text. Locked notes only match on title (their body is never
    substring-matched, so a search hit can't leak hidden content)."""
    return _get_client().get("/notes/search", {"q": q, "limit": limit})


@mcp.tool()
def get_note_stats() -> dict[str, Any]:
    """Aggregate stats: total active notes, total storage bytes used,
    pinned-note count, and a created-at histogram by day."""
    return _get_client().get("/notes/stats")


@mcp.tool()
def list_note_recipients(note_id: str) -> dict[str, Any]:
    """List who a note (owned by the caller) has been shared with."""
    return _get_client().get(f"/notes/{note_id}/recipients")


@mcp.tool()
def list_shared_notes() -> dict[str, Any]:
    """List notes that have been shared with the caller by someone else
    (received copies), most recently shared first."""
    return _get_client().get("/shared")


@mcp.tool()
def list_folders(include_trashed: bool = False) -> dict[str, Any]:
    """List the caller's notebooks/folders."""
    return _get_client().get("/folders", {"include_trashed": include_trashed})


@mcp.tool()
def get_folder(folder_id: str) -> dict[str, Any]:
    """Get a single folder by id."""
    return _get_client().get(f"/folders/{folder_id}")


@mcp.tool()
def list_tags() -> dict[str, Any]:
    """List every tag used across the caller's active notes."""
    return _get_client().get("/tags")


def run() -> None:
    mcp.run(transport="stdio")
