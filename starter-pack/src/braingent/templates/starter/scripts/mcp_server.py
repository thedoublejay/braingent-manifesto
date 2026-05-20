#!/usr/bin/env python3
"""Compatibility wrapper for the packaged Braingent MCP server."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SCRIPT_DIR) in sys.path:
    sys.path.remove(str(SCRIPT_DIR))
if SRC_DIR.is_dir() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from braingent.mcp_server import main

if __name__ == "__main__":
    warnings.warn(
        "scripts/mcp_server.py is a compatibility wrapper; prefer `braingent mcp serve` or `braingent-mcp`.",
        DeprecationWarning,
        stacklevel=2,
    )
    main()
