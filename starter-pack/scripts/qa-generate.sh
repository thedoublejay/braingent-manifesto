#!/usr/bin/env sh
set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
script="$repo_root/tools/tool--test-plan/test_plan.py"

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$script" "$@"
fi

if command -v uv >/dev/null 2>&1; then
  exec uv run --script "$script" "$@"
fi

printf '%s\n' 'Missing runtime: install python3 or uv.' >&2
exit 127
