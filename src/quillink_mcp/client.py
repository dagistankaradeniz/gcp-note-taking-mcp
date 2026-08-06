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
        resp.raise_for_status()
        return resp.json()

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params)
