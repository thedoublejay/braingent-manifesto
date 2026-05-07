"""Filtering compressors for predictable low-signal sections."""

from __future__ import annotations

import re

ARCHIVE_HEADERS = {"Archived", "Archive", "Old", "Stale", "Deprecated"}


def frontmatter_only(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[: end + 5]


def drop_archived_sections(text: str, *, record_kind: str) -> str:
    result = _drop_named_sections(text, ARCHIVE_HEADERS)
    if record_kind == "task" and re.search(r"^status:\s*closed\s*$", result, re.MULTILINE):
        result = _drop_named_sections(result, {"Playbook"})
    return result


def _drop_named_sections(text: str, headings: set[str]) -> str:
    out: list[str] = []
    skip = False
    for line in text.splitlines(keepends=True):
        heading = _h2_heading(line)
        if heading is not None:
            skip = heading in headings
        if not skip:
            out.append(line)
    return "".join(out)


def _h2_heading(line: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith("## "):
        return None
    return stripped[3:].strip()
