"""Grouping compressors for repeated link-list patterns."""

from __future__ import annotations

import re

LINK_LINE = re.compile(r"^- \[.+?\]\(.+?\)\s*$")


def collapse_link_lists(text: str, threshold: int = 3) -> str:
    out: list[str] = []
    run: list[str] = []

    def flush() -> None:
        if len(run) > threshold:
            out.append(run[0])
            out.append(f"- ... (+{len(run) - 1} more links collapsed)\n")
        else:
            out.extend(run)
        run.clear()

    for line in text.splitlines(keepends=True):
        if LINK_LINE.match(line.rstrip("\n")):
            run.append(line)
            continue
        flush()
        out.append(line)
    flush()
    return "".join(out)
