# Issue 008: Expand Greenhouse/Lever board seed list

**Labels:** `ready-for-agent`  
**Type:** AFK  
**Blocked by:** #002

## Parent

[PRD: AI Internship Intelligence Agent v1](../PRD-internship-intelligence-v1.md)

## What to build

Add a configurable seed file (boards + optional manual URLs) consumed at discovery startup, complementing existing `--internship-url` and `--internship-urls-file` flags. Document the format (one entry per line, comments with `#`).

Discovery logs how many listings each seed contributed. Works with hybrid cache and lenient filters.

## Acceptance criteria

- [ ] Seed config file path configurable via CLI (sensible default)
- [ ] Greenhouse and Lever board slugs/URLs from seed file are discovered
- [ ] Manual URLs in seed file still supported
- [ ] Format documented with example file in repo
- [ ] Discovery logs per-source counts including seeds
- [ ] End-to-end discover with seed file increases raw cache size vs no seeds

## Blocked by

- #002 — Hybrid cache replay (no sample fallback by default)
