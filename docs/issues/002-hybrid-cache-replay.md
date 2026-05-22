# Issue 002: Hybrid cache replay (no sample fallback by default)

**Labels:** `ready-for-agent`  
**Type:** AFK  
**Blocked by:** #001

## Parent

[PRD: AI Internship Intelligence Agent v1](../PRD-internship-intelligence-v1.md)

## What to build

Extend hybrid discovery so the pipeline always saves **raw** listings to the cache before filtering. When live discovery completes but the **filtered** set is empty (and `--live` is not set), **reload** the cached raw dataset and re-apply the current filter policy (strict or lenient).

Remove or gate fabricated **sample fallback** internships behind an explicit dev-only flag; normal runs prefer real cached data over samples.

Add tests: empty live filtered + non-empty cache → replay produces ranked output; `--live` skips replay and sample fallback.

## Acceptance criteria

- [ ] Raw listings persist to cache on every discovery run
- [ ] Empty post-filter live result triggers cache replay when not `--live`
- [ ] Replay respects current filter mode from settings
- [ ] Sample fallback disabled by default; dev flag documented if retained
- [ ] Tests verify cache replay path and `--live` behavior
- [ ] Discover/lenient run after failed live scrape still yields non-empty reports when cache has data

## Blocked by

- #001 — Lenient filters + rank penalty for unknown stipend/duration
