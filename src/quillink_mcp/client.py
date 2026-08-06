"""Thin wrapper over the /v1 REST API -- the same programmatic surface
the CLI and Developer-page "Try it" panel use, authenticated with a Bearer
credential (PAT or OAuth token, see auth.py)."""

from __future__ import annotations

from typing import Any

import httpx

from . import auth


class QuillinkClient:
    def __init__(self) -> None:
        self._base = auth.api_base()
        self._token = auth.require_token()

    def _request(self, method: str, path: str, params: dict[str, Any] | None = None) -> Any:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        with httpx.Client(base_url=self._base, timeout=30.0) as client:
            resp = client.request(
                method,
                f"/v1{path}",
                params=params,
                headers={"Authorization": f"Bearer {self._token}"},
            )
        if resp.status_code == 401:
            raise RuntimeError(
                "Quillink API rejected the credential (expired or revoked). "
                "Run `quillink-mcp login` again, or check QUILLINK_TOKEN."
            )
        if resp.status_code >= 400:
            # Surface the API's own RFC 7807 `detail` (e.g. "Note not
            # found") instead of a generic httpx status-line message --
            # far more useful for an agent deciding what to do next.
            try:
                detail = resp.json().get("detail")
            except ValueError:
                detail = None
            raise RuntimeError(detail or f"{resp.status_code} {resp.reason_phrase}")
        return resp.json()

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params)
