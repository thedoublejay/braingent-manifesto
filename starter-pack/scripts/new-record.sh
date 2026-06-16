#!/usr/bin/env sh
set -eu

usage() {
  printf '%s\n' 'Usage: scripts/new-record.sh <record-kind> <entity-key> <subject> <output-dir> [suffix]'
  printf '%s\n' 'Example: scripts/new-record.sh task project--example--memory "import baseline notes" orgs/org--example/projects/project--example--memory/records'
  printf '%s\n' 'Set BRAINGENT_TIMEZONE to override the default timezone (Asia/Singapore).'
}

if [ "$#" -lt 4 ] || [ "$#" -gt 5 ]; then
  usage
  exit 2
fi

record_kind="$1"
entity_key="$2"
subject="$3"
output_dir="$4"
suffix="${5:-}"

case "$record_kind" in
  task|review|decision|learning|interaction|version|note|summary|profile|ticket-stub) ;;
  *)
    printf 'Invalid record kind: %s\n' "$record_kind" >&2
    exit 2
    ;;
esac

template_for_kind() {
  case "$1" in
    task) printf '%s\n' 'task-record.md' ;;
    review) printf '%s\n' 'code-review-record.md' ;;
    decision) printf '%s\n' 'decision-record.md' ;;
    learning) printf '%s\n' 'learning-record.md' ;;
    interaction) printf '%s\n' 'person-interaction-record.md' ;;
    version) printf '%s\n' 'tool-version-record.md' ;;
    note) printf '%s\n' 'note-record.md' ;;
    summary) printf '%s\n' 'import-summary-record.md' ;;
    profile) printf '%s\n' 'repository-profile.md' ;;
    ticket-stub) printf '%s\n' 'ticket-stub.md' ;;
  esac
}

slugify() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed 's/[^a-z0-9][^a-z0-9]*/-/g; s/^-//; s/-$//; s/--*/-/g'
}

subject_slug="$(slugify "$subject")"

if [ -z "$subject_slug" ]; then
  printf '%s\n' 'Subject must contain at least one ASCII letter or digit.' >&2
  exit 2
fi

date_today="$(date +%Y-%m-%d)"
tz="${BRAINGENT_TIMEZONE:-${TZ:-Asia/Singapore}}"
if [ -n "$suffix" ]; then
  suffix_slug="$(slugify "$suffix")"
  if [ -z "$suffix_slug" ]; then
    printf '%s\n' 'Suffix must contain at least one ASCII letter or digit.' >&2
    exit 2
  fi
  subject_slug="${subject_slug}--${suffix_slug}"
fi

filename="${date_today}--${record_kind}--${subject_slug}.md"
path="${output_dir%/}/${filename}"

mkdir -p "$output_dir"

if [ -e "$path" ]; then
  counter=2
  while :; do
    filename="${date_today}--${record_kind}--${subject_slug}--${counter}.md"
    path="${output_dir%/}/${filename}"
    if [ ! -e "$path" ]; then
      break
    fi
    counter=$((counter + 1))
  done
fi

title="$(printf '%s' "$subject" | sed 's/[[:space:]][[:space:]]*/ /g; s/^ //; s/ $//')"

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
template_path="$repo_root/templates/$(template_for_kind "$record_kind")"
if [ ! -f "$template_path" ]; then
  printf 'Missing template for %s: %s\n' "$record_kind" "$template_path" >&2
  exit 1
fi

organization="null"
project="null"
repo="null"
topic="null"
tool="null"
person="null"
ticket="null"
ticket_system="other"

case "$entity_key" in
  org--*)
    organization="$entity_key"
    ;;
  project--*)
    project="$entity_key"
    project_scope="${entity_key#project--}"
    project_scope="${project_scope%%--*}"
    organization="org--$project_scope"
    ;;
  repo--*)
    repo="$entity_key"
    repo_tail="${entity_key#repo--}"
    repo_tail="${repo_tail#*--}"
    repo_owner="${repo_tail%%--*}"
    [ -z "$repo_owner" ] || organization="org--$repo_owner"
    ;;
  topic--*)
    topic="$entity_key"
    ;;
  tool--*)
    tool="$entity_key"
    ;;
  person--*)
    person="$entity_key"
    ;;
  ticket--*)
    ticket_rest="${entity_key#ticket--}"
    ticket_system="${ticket_rest%%--*}"
    ticket_value="${ticket_rest#*--}"
    ticket="$(printf '%s' "$ticket_value" | tr '[:lower:]' '[:upper:]')"
    ;;
  *-*)
    ticket="$(printf '%s' "$entity_key" | tr '[:lower:]' '[:upper:]')"
    ;;
esac

repositories_list="[]"
topics_list="[]"
tools_list="[]"
people_list="[]"
projects_list="[]"
[ "$repo" = "null" ] || repositories_list="[$repo]"
[ "$topic" = "null" ] || topics_list="[$topic]"
[ "$tool" = "null" ] || tools_list="[$tool]"
[ "$person" = "null" ] || people_list="[$person]"
[ "$project" = "null" ] || projects_list="[$project]"

sed_escape() {
  printf '%s' "$1" | sed 's/[\\&|]/\\&/g'
}

yaml_double_quoted() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/[[:cntrl:]]//g'
}

title_sed="$(sed_escape "$title")"
title_yaml="$(sed_escape "$(yaml_double_quoted "$title")")"
tz_sed="$(sed_escape "$tz")"
date_sed="$(sed_escape "$date_today")"
organization_sed="$(sed_escape "$organization")"
project_sed="$(sed_escape "$project")"
repo_sed="$(sed_escape "$repo")"
topic_sed="$(sed_escape "$topic")"
tool_sed="$(sed_escape "$tool")"
person_sed="$(sed_escape "$person")"
ticket_sed="$(sed_escape "$ticket")"
ticket_system_sed="$(sed_escape "$ticket_system")"
repositories_list_sed="$(sed_escape "$repositories_list")"
topics_list_sed="$(sed_escape "$topics_list")"
tools_list_sed="$(sed_escape "$tools_list")"
people_list_sed="$(sed_escape "$people_list")"
projects_list_sed="$(sed_escape "$projects_list")"

if ! sed \
  -e "s|^title: <title>$|title: \"$title_yaml\"|" \
  -e "s|^title: <source and scope>$|title: \"$title_yaml\"|" \
  -e "s|^title: <repo name>$|title: \"$title_yaml\"|" \
  -e "s|^title: <ticket id and short subject>$|title: \"$title_yaml\"|" \
  -e "s|^title: <tool or framework>$|title: \"$title_yaml\"|" \
  -e "s|<title>|$title_sed|g" \
  -e "s|<source and scope>|$title_sed|g" \
  -e "s|<repo name>|$title_sed|g" \
  -e "s|<ticket id and short subject>|$title_sed|g" \
  -e "s|<tool or framework>|$title_sed|g" \
  -e "s|<yyyy-mm-dd>|$date_sed|g" \
  -e "s|<yyyy-mm-dd-or-null>|null|g" \
  -e "s|<timezone>|$tz_sed|g" \
  -e "s|<org-key-or-null>|$organization_sed|g" \
  -e "s|<org-key-or-personal>|$organization_sed|g" \
  -e "s|<org-key>|$organization_sed|g" \
  -e "s|<project-key-or-null>|$project_sed|g" \
  -e "s|<project-key>|$project_sed|g" \
  -e "s|<repo-key>|$repo_sed|g" \
  -e "s|<topic-key>|$topic_sed|g" \
  -e "s|<tool-key>|$tool_sed|g" \
  -e "s|<person-key-or-tool>|Codex|g" \
  -e "s|<person-or-tool>|Codex|g" \
  -e "s|<person-key>|$person_sed|g" \
  -e "s|<ticket-id-or-null>|$ticket_sed|g" \
  -e "s|<ticket-id>|$ticket_sed|g" \
  -e "s#<jira | github | linear | other>#$ticket_system_sed#g" \
  -e "s|<url-or-null>|null|g" \
  -e "s#<PR | branch | commit | diff | design-doc>#diff#g" \
  -e "s#<Slack | meeting | PR | Jira | email | chat>#chat#g" \
  -e "s#<global | org | project | repo>#repo#g" \
  -e "s#<file | command | docs | lockfile>#command#g" \
  -e "s#<Claude | Codex | ChatGPT | Jira | GitHub | local-docs | other>#Codex#g" \
  -e "s#<date-range | project | repo | ticket>#project#g" \
  -e "s|<path or link>|null|g" \
  -e "s|repositories: \\[\\]|repositories: $repositories_list_sed|" \
  -e "s|topics: \\[\\]|topics: $topics_list_sed|" \
  -e "s|tools: \\[\\]|tools: $tools_list_sed|" \
  -e "s|people: \\[\\]|people: $people_list_sed|" \
  -e "s|projects: \\[\\]|projects: $projects_list_sed|" \
  "$template_path" > "$path"
then
  printf 'Failed to write record: %s\n' "$path" >&2
  exit 1
fi

printf '%s\n' "$path"
