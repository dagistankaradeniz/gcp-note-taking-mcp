"""CLI entrypoint. Running `quillink-mcp` with no arguments starts the MCP
server itself (stdio transport, what an MCP client like Claude Desktop
actually invokes) -- `login`/`logout` are one-off setup/maintenance
commands a person runs by hand, mirroring `quillink login`/`quillink
logout` in the CLI."""

from __future__ import annotations

import argparse
import os
import sys

from . import auth
from .server import run as run_server


def main() -> None:
    parser = argparse.ArgumentParser(prog="quillink-mcp")
    subparsers = parser.add_subparsers(dest="command")
    login = subparsers.add_parser("login", help="Sign in via the browser (OAuth device flow)")
    login.add_argument(
        "--no-browser",
        action="store_true",
        help="print the sign-in link instead of opening the browser",
    )
    subparsers.add_parser("logout", help="Forget the stored credential")
    args = parser.parse_args()

    if args.command == "login":
        auth.device_login(
            open_browser=not args.no_browser and not os.environ.get("QUILLINK_NO_BROWSER")
        )
        print("Logged in.", file=sys.stderr)
        return
    if args.command == "logout":
        auth.delete_token()
        print("Logged out.", file=sys.stderr)
        return

    run_server()


if __name__ == "__main__":
    main()
