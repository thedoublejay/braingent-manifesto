#!/usr/bin/env sh
set -eu

usage() {
  printf '%s\n' 'Usage: scripts/cleanup.sh [--daily|--weekly|--monthly|--quarterly|--standard|--deep] [--strict]'
}

mode="standard"
strict=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --daily) mode="daily" ;;
    --weekly) mode="weekly" ;;
    --monthly) mode="monthly" ;;
    --quarterly) mode="quarterly" ;;
    --standard) mode="standard" ;;
    --deep) mode="deep" ;;
    --strict) strict=1 ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
  shift
done

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$repo_root"

run() {
  printf '\n$'
  printf ' %s' "$@"
  printf '\n'
  "$@"
}

run_optional() {
  printf '\n$'
  printf ' %s' "$@"
  printf '\n'
  set +e
  "$@"
  status="$?"
  set -e
  if [ "$status" -eq 0 ]; then
    return 0
  fi
  printf 'optional command exited %s\n' "$status"
  return 0
}

printf '# Braingent Cleanup\n\n'
printf 'Mode: %s\n' "$mode"
printf 'Strict: %s\n' "$strict"

run git status --short
if [ "$strict" -eq 1 ]; then
  run scripts/doctor.sh --strict
else
  run scripts/doctor.sh
fi
run scripts/validate.sh
run scripts/reindex.sh --check

case "$mode" in
  weekly|monthly|quarterly|deep|standard)
    run_optional scripts/find.sh status=active --count
    run_optional scripts/task-list.sh --count
    run_optional cat indexes/stale-candidates.md
    run_optional rg -n '^- \[ \]' --type md orgs repositories topics tools tickets inbox imports
    run_optional rg -n '^last_reviewed: 2025-|^last_revalidated: 2025-' .
    run_optional rg -n '^raw_retained_until:' imports orgs topics repositories tools tickets inbox
    ;;
esac

case "$mode" in
  monthly|quarterly|deep)
    run_optional find synthesis -maxdepth 3 -type f
    printf '\nMonthly/deep synthesis refresh is report-only here. Run scripts/synthesize.sh for a chosen --topic, --repo, or --project after reviewing source records.\n'
    ;;
esac

printf '\nCleanup checks completed.\n'
