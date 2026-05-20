"""Compression pipeline for token-efficient Braingent hydration."""

from __future__ import annotations

from . import dedupe, filters, group, truncate
from .base import Depth

VALID_DEPTHS = {"full", "summary", "frontmatter"}


def apply_pipeline(
    text: str,
    *,
    record_kind: str,
    depth: str,
) -> str:
    if depth not in VALID_DEPTHS:
        raise ValueError(f"unknown depth: {depth}")
    if depth == "frontmatter":
        return filters.frontmatter_only(text)
    if depth == "full":
        return text

    out = filters.drop_archived_sections(text, record_kind=record_kind)
    out = group.collapse_link_lists(out)
    out = dedupe.collapse_repeated_lines(out)
    out = truncate.head_per_section(out, max_lines_per_section=20)
    return out


__all__ = ["VALID_DEPTHS", "Depth", "apply_pipeline"]
