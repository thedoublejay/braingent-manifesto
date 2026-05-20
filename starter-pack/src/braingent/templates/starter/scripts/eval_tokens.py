#!/usr/bin/env python3
"""Token measurement helpers for Braingent artifacts."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

DEFAULT_ENCODING = "cl100k_base"
_ENCODINGS: dict[str, Any] = {}


def _encoding_for(name: str) -> Any | None:
    if name in _ENCODINGS:
        return _ENCODINGS[name]
    try:
        import tiktoken  # type: ignore[import-not-found]
    except ImportError:
        _ENCODINGS[name] = None
        return None
    encoding = tiktoken.get_encoding(name)
    _ENCODINGS[name] = encoding
    return encoding


def count_tokens(text: str, encoding_name: str = DEFAULT_ENCODING) -> int:
    if not text:
        return 0
    encoding = _encoding_for(encoding_name)
    if encoding is not None:
        return len(encoding.encode(text))
    return len(re.findall(r"\w+|[^\w\s]", text, re.UNICODE))


def tokenizer_name(encoding_name: str = DEFAULT_ENCODING) -> str:
    return encoding_name if _encoding_for(encoding_name) is not None else "regex-fallback"


def measure_session(paths: Iterable[str | Path], encoding_name: str = DEFAULT_ENCODING) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        text = path.read_text(encoding="utf-8")
        files.append(
            {
                "path": path.as_posix(),
                "bytes": len(text.encode("utf-8")),
                "tokens": count_tokens(text, encoding_name),
            }
        )
    return {
        "encoding": tokenizer_name(encoding_name),
        "total_bytes": sum(item["bytes"] for item in files),
        "total_tokens": sum(item["tokens"] for item in files),
        "per_file": {item["path"]: item["tokens"] for item in files},
        "files": files,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Measure token cost for Braingent files.")
    parser.add_argument("paths", nargs="+", help="files to measure")
    parser.add_argument("--encoding", default=DEFAULT_ENCODING, help="tiktoken encoding name")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = measure_session(args.paths, args.encoding)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print(f"encoding: {result['encoding']}")
    print(f"total_tokens: {result['total_tokens']}")
    print(f"total_bytes: {result['total_bytes']}")
    for item in result["files"]:
        print(f"{item['tokens']}\t{item['bytes']}\t{item['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
