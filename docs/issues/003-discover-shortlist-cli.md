# Issue 003: `discover` and `shortlist` CLI run profiles

**Labels:** `ready-for-agent`  
**Type:** AFK  
**Blocked by:** #001

## Parent

[PRD: AI Internship Intelligence Agent v1](../PRD-internship-intelligence-v1.md)

## What to build

Add `discover` and `shortlist` subcommands to the CLI via a `RunProfile` (or equivalent) that maps each command to preset `AgentSettings`:

| | discover | shortlist |
|---|----------|-----------|
| Filter | lenient | strict |
| Rich reports | off | on (wired in #005) |
| limit / top_k | 30 / 10 | 30 / 5 |

Explicit flags continue to override presets. Extend settings with `filter_mode` and `rich_reports`.

Add tests asserting preset → settings mapping. Document both commands in project docs.

## Acceptance criteria

- [ ] `python main.py discover --resume <pdf>` runs with lenient filter preset
- [ ] `python main.py shortlist --resume <pdf>` runs with strict filter preset
- [ ] `--lenient`, `--min-stipend`, `--top-k`, etc. override presets when passed
- [ ] `RunProfile` tests cover discover vs shortlist defaults
- [ ] CLI help text describes when to use each command
- [ ] End-to-end discover produces reports; shortlist uses stricter filtering

## Blocked by

- #001 — Lenient filters + rank penalty for unknown stipend/duration
