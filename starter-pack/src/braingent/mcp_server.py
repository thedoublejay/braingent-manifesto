#!/usr/bin/env python3
"""braingent-mcp server entrypoint."""

from __future__ import annotations

import argparse

try:
    from mcp.server.mcpserver import MCPServer
except ImportError as exc:  # pragma: no cover - depends on optional runtime.
    raise SystemExit("Missing dependency `mcp`. Install with `pipx inject braingent 'mcp>=2.2.0'`.") from exc

from braingent import core, mcp_tools

mcp = MCPServer("braingent")


@mcp.tool()
def braingent_find(query: dict | None = None, limit: int = 10) -> list[dict]:
    """Search Braingent records by frontmatter fields.

    Prefer this over reading indexes/records.json or indexes/records.md.
    Empty queries return the compact generated index prefix. Filter by epic
    with {"epic": "<slug or epic-- id>"}.
    """

    return mcp_tools.find(query=query, limit=limit)


@mcp.tool()
def braingent_search(query: str, filters: dict | None = None, limit: int = 8) -> list[dict]:
    """Ranked full-text search when you do not know the exact labels.

    Any word may match; ticket keys and PR references rank first when they are
    in a record's metadata. `filters` takes the same keys as braingent_find.
    Check each hit's `class` before relying on it: `do_not_use` is superseded,
    and `reference` is a read-only document from a configured corpus such as
    plans (open it with its `file` path; braingent_get does not read it).
    """

    return mcp_tools.search(query=query, filters=filters, limit=limit)


@mcp.tool()
def braingent_get(path: str, depth: str = "summary") -> dict:
    """Hydrate one Braingent record.

    depth is "summary", "full", or "frontmatter". Summary is the default
    cheap path.
    """

    return mcp_tools.get(path=path, depth=depth)


@mcp.tool()
def braingent_guide() -> dict:
    """Return the cache-stable read-first guidance chain."""

    return mcp_tools.guide()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Serve Braingent MCP tools over stdio.")
    parser.add_argument("--root", "--path", dest="root", help="Braingent repo root to serve")
    args = parser.parse_args(argv)
    if args.root:
        core.set_repo_root(args.root)
    mcp.run()


if __name__ == "__main__":
    main()
