#!/usr/bin/env python3
"""braingent-mcp server entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - depends on optional runtime.
    raise SystemExit("Missing dependency `mcp`. Install with `python3 -m pip install -r requirements.txt`.") from exc

from scripts import mcp_tools

mcp = FastMCP("braingent")


@mcp.tool()
def braingent_find(query: dict | None = None, limit: int = 10) -> list[dict]:
    """Search Braingent records by frontmatter fields.

    Prefer this over reading indexes/records.json or indexes/records.md.
    Empty queries return the compact generated index prefix.
    """

    return mcp_tools.find(query=query, limit=limit)


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


if __name__ == "__main__":
    mcp.run()
