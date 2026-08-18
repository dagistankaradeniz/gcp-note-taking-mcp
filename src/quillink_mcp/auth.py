"""Credential resolution and the OAuth 2.0 Device Authorization Grant login
flow -- mirrors gcp-note-taking-cli's internal/auth package so the two
tools behave identically, just in Python instead of Go. Kept in its own
keyring service ("quillink-mcp", not "quillink-cli") since this server
requests a narrower, read-only scope set than the CLI does.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx
import keyring
from keyring.errors import KeyringError

KEYRING_SERVICE = "quillink-mcp"
KEYRING_USER = "default"

# v1's client_id registration is a manual, per-environment admin step (see
# app/routers/oauth.py's get_client / POST /api/admin/oauth-clients) -- the
# same placeholder-until-registered state gcp-note-taking-cli's own
# CLIClientID is in. Override with QUILLINK_CLIENT_ID once a real client
# is registered for this tool.
DEFAULT_CLIENT_ID = "REPLACE_WITH_REGISTERED_CLIENT_ID"
DEFAULT_API_BASE = "https://note-taking-app-prod.web.app"

# Read-only: no notes:write/folders:write/tags:write/organizations:write,
# matching this server's tool set (see server.py -- no create/update/
# trash/invite/role-change tools).
SCOPES = ["notes:read", "folders:read", "tags:read", "organizations:read"]


def api_base() -> str:
    return os.environ.get("QUILLINK_API_BASE", DEFAULT_API_BASE).rstrip("/")


def client_id() -> str:
    return os.environ.get("QUILLINK_CLIENT_ID", DEFAULT_CLIENT_ID)


def _credential_file() -> Path:
    return Path.home() / ".config" / "quillink-mcp" / "credential"


def save_token(token: str) -> None:
    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, token)
        return
    except KeyringError:
        pass
    path = _credential_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token)
    path.chmod(0o600)


def load_token() -> str | None:
    """Resolution order: QUILLINK_TOKEN env var (a PAT, for quick/CI use)
    -> OS keyring -> credential file -> None (caller should run login())."""
    env_token = os.environ.get("QUILLINK_TOKEN")
    if env_token:
        return env_token
    try:
        token = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
        if token:
            return token
    except KeyringError:
        pass
    path = _credential_file()
    if path.exists():
        return path.read_text().strip()
    return None


def delete_token() -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
    except KeyringError:
        pass
    path = _credential_file()
    if path.exists():
        path.unlink()


def device_login() -> str:
    """Runs RFC 8628 device authorization: request a code, print it for
    the user, poll until they approve it in a browser. Mirrors the CLI's
    auth.Login exactly (same endpoints, same polling/backoff behavior)."""
    base = api_base()
    with httpx.Client(base_url=base, timeout=30.0) as client:
        code_resp = client.post(
            "/api/oauth/device/code",
            json={"client_id": client_id(), "scope": SCOPES},
        )
        code_resp.raise_for_status()
        code = code_resp.json()

        print(
            f"Go to {code['verification_uri']} and enter code: {code['user_code']}",
            file=sys.stderr,
        )
        print(f"Or open {code['verification_uri_complete']} directly.", file=sys.stderr)
        print("Waiting for confirmation...", file=sys.stderr)

        interval = code.get("interval") or 5
        deadline = time.time() + code.get("expires_in", 600)

        while time.time() < deadline:
            time.sleep(interval)
            token_resp = client.post(
                "/api/oauth/device/token",
                json={
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": code["device_code"],
                    "client_id": client_id(),
                },
            )
            if token_resp.status_code == 200:
                token = token_resp.json()["access_token"]
                save_token(token)
                return token

            detail = token_resp.json().get("detail", "")
            if detail == "authorization_pending":
                continue
            if detail == "slow_down":
                interval += 5
                continue
            if detail == "access_denied":
                raise RuntimeError("Login denied in the browser.")
            raise RuntimeError(f"Device login failed: {detail or token_resp.text}")

    raise RuntimeError("Device code expired before login was confirmed.")


def require_token() -> str:
    token = load_token()
    if token:
        return token
    print("Not logged in -- starting device login.", file=sys.stderr)
    return device_login()
