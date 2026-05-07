"""Shared compressor types."""

from __future__ import annotations

from typing import Literal, Protocol

Depth = Literal["full", "summary", "frontmatter"]


class Compressor(Protocol):
    def apply(self, text: str, *, record_kind: str, depth: Depth) -> str:
        """Return compressed Markdown for one record."""
