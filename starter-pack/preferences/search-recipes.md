# Search Recipes

Use search before planning or answering from memory.

## Free Text

```bash
rg -n "<query>" .
```

Examples:

```bash
rg -n "authentication|auth guard|login" .
rg -n "record_kind: decision" .
rg -n "status: active" .
rg -n "ticket: <ticket-id>" .
```

## By Record Kind

```bash
rg -n "record_kind: task" .
rg -n "record_kind: review" .
rg -n "record_kind: decision" .
rg -n "record_kind: learning" .
```

## By Status

```bash
rg -n "status: active" .
rg -n "status: blocked" .
rg -n "status: superseded" .
```

## By Repository

```bash
rg -n "repo--github--owner--repo-name" .
```

## By Topic Or Tool

```bash
rg -n "topic--testing" .
rg -n "tool--node" .
```

## By Follow-Up

```bash
rg -n "^- \\[ \\]" .
```

## By Date

```bash
rg -n "date: 2026-04-26" .
```

## Safety Sweep

```bash
rg -n "token|secret|password|api_key|apikey|private key" .
```

Search results are leads, not proof. Read the matching files before making decisions.

