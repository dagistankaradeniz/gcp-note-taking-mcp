"""The Quillink MCP server: read-only tools over notes, folders, tags,
attachments, search, and (Team-plan) organizations. Deliberately no write
tools in this first release (create/update/trash notes or folders;
upload/delete attachments; invite/remove members, role or seat changes) --
keeps an AI agent from being able to modify or delete a user's notes or
organization; see the Developer > MCP page for the plan to add a
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
def get_note_backlinks(note_id: str) -> dict[str, Any]:
    """List notes that link to note_id, each with an id/title/snippet.
    Fails with 403 if note_id isn't owned by the caller, 404 if it doesn't
    exist."""
    return _get_client().get(f"/notes/{note_id}/backlinks")


@mcp.tool()
def get_related_notes(note_id: str, limit: int = 5) -> dict[str, Any]:
    """Tag/link-similarity "you might want to link these" suggestions for
    note_id: other notes/canvases ranked by a similarity score, with the
    tags they share. Requires a Pro plan, same gate as note_graph/
    note_backlinks. Fails with 403 if note_id isn't owned by the caller,
    404 if it doesn't exist."""
    return _get_client().get(f"/notes/{note_id}/related", {"limit": limit})


@mcp.tool()
def get_note_graph(note_id: str, hops: int = 1) -> dict[str, Any]:
    """Local link graph centered on note_id: nodes (id/title/locked) and
    edges (source -> target) for its direct links and backlinks. hops=1 is
    direct neighbors only; hops=2 also expands each neighbor's own
    neighbors one level further."""
    return _get_client().get(f"/notes/{note_id}/graph", {"hops": hops})


@mcp.tool()
def get_global_note_graph(cursor: str | None = None, limit: int = 100) -> dict[str, Any]:
    """Whole-account link graph, paginated: nodes and edges across every
    note that has at least one link (in or out) or is locked. Pass the
    response's next_cursor back in to fetch the next page; None means the
    graph is exhausted. Requires a Pro plan, same gate as the web app's
    Global Graph feature."""
    return _get_client().get("/notes/graph/global", {"cursor": cursor, "limit": limit})


@mcp.tool()
def get_graph_analysis(
    community_algo: str = "louvain", centrality_algo: str = "pagerank"
) -> dict[str, Any]:
    """Community detection + importance ranking over the caller's whole
    account graph. community_algo: "louvain" (default), "label_propagation",
    "greedy_modularity", or "connected_components". centrality_algo:
    "pagerank" (default), "betweenness", "degree", or "closeness". Requires
    a Pro plan, same gate as get_global_note_graph. On a very large graph
    the response may note that a cheaper approximation was substituted for
    the exact algorithm requested."""
    return _get_client().get(
        "/notes/graph/global/analysis",
        {"community_algo": community_algo, "centrality_algo": centrality_algo},
    )


@mcp.tool()
def export_note(note_id: str) -> str:
    """A single note rendered as a standalone Markdown file (title as an
    H1, followed by the body). A locked note's body can't be exported
    without its password -- returns just the title with a note explaining
    why. Fails with 403/404 same as get_note."""
    return _get_client().get_text(f"/notes/{note_id}/export")


@mcp.tool()
def export_notes(
    format: str = "ndjson",
    folder_id: str | None = None,
    tags: list[str] | None = None,
    limit: int = 5000,
) -> str:
    """Bulk export of the caller's active notes -- for backups/scripting,
    not paged browsing (use list_notes for that). format="ndjson"
    (default) returns one full note object per line; format="markdown"
    returns one "# Title" block per note, concatenated into a single
    document. Locked notes are included with their body withheld, same as
    list_notes."""
    return _get_client().get_text(
        "/notes/export",
        {"format": format, "folder_id": folder_id, "tags": tags, "limit": limit},
    )


@mcp.tool()
def list_attachments(note_id: str) -> dict[str, Any]:
    """List a note's file attachments. Fails with 403 if note_id isn't
    owned by the caller, 404 if it doesn't exist."""
    return _get_client().get(f"/notes/{note_id}/attachments")


@mcp.tool()
def get_attachment_download_url(note_id: str, attachment_id: str) -> dict[str, Any]:
    """A short-lived signed URL to download one attachment's file bytes
    directly (not through this tool) -- expires_in seconds from now. A ZK/
    Vault/lock-encrypted note's attachment is still opaque ciphertext at
    that URL; there's no decrypt path here, same as a locked note's body."""
    return _get_client().get(f"/notes/{note_id}/attachments/{attachment_id}/download")


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
def list_tags() -> list[str]:
    """List every tag used across the caller's active notes."""
    return _get_client().get("/tags")


@mcp.tool()
def get_organization() -> dict[str, Any]:
    """Get the caller's Team-plan organization: name, plan tier, seat
    allocations, member count, and any active alerts. 404s if the caller
    doesn't belong to a Team-plan organization."""
    return _get_client().get("/organizations/me")


@mcp.tool()
def list_organization_members() -> list[dict[str, Any]]:
    """List the caller's organization's members. A plain member sees only
    their own entry -- other members' emails/names/roles are admin/owner-
    only information, scoped the same way the web app scopes it."""
    return _get_client().get("/organizations/me/members")


def run() -> None:
    mcp.run(transport="stdio")
