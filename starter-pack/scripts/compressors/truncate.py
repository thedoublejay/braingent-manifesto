"""Heading-aware truncation compressors."""

from __future__ import annotations


def head_per_section(text: str, *, max_lines_per_section: int) -> str:
    if max_lines_per_section < 1:
        raise ValueError("max_lines_per_section must be greater than zero")

    sections: list[list[str]] = [[]]
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            sections.append([line])
        else:
            sections[-1].append(line)

    out: list[str] = []
    for section in sections:
        if not section:
            continue
        header_count = 1 if section[0].startswith("## ") else 0
        body = section[header_count:]
        if len(body) <= max_lines_per_section:
            out.extend(section)
            continue
        dropped = len(body) - max_lines_per_section
        out.extend(section[:header_count] + body[:max_lines_per_section])
        out.append(f"\n_... ({dropped} more lines truncated)_\n")
    return "".join(out)
