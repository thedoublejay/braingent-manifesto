"""Deduplication compressors."""

from __future__ import annotations


def collapse_repeated_lines(text: str) -> str:
    out: list[str] = []
    previous: str | None = None
    repeat_count = 0

    for line in text.splitlines(keepends=True):
        if line == previous:
            repeat_count += 1
            continue
        if previous is not None and repeat_count > 0:
            out[-1] = out[-1].rstrip("\n") + f"  (repeated {repeat_count + 1}x)\n"
        out.append(line)
        previous = line
        repeat_count = 0

    if previous is not None and repeat_count > 0:
        out[-1] = out[-1].rstrip("\n") + f"  (repeated {repeat_count + 1}x)\n"
    return "".join(out)
