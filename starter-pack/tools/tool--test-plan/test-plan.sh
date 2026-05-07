#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
script="$script_dir/test_plan.py"

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$script" "$@"
fi

if command -v uv >/dev/null 2>&1; then
  exec uv run --script "$script" "$@"
fi

echo "test-plan: python3 or uv is required" >&2
exit 127
