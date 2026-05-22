# Issue 007: Internshala discovery source

**Labels:** `ready-for-agent`  
**Type:** AFK  
**Blocked by:** #002

## Parent

[PRD: AI Internship Intelligence Agent v1](../PRD-internship-intelligence-v1.md)

## What to build

Implement an Internshala scraper integrated into live discovery, producing `Internship` records with India-relevant metadata (stipend, duration where available). Respect existing HTTP client patterns (retries, logging). Add fixture-based tests without live network dependency in CI.

Wire into `InternshipScraper` source list so `discover` runs can populate cache from Internshala.

## Acceptance criteria

- [ ] Internshala listings merge into discovery with `source=internshala`
- [ ] Stipend/duration parsed when present in listing HTML/JSON
- [ ] Scraper failures log gracefully without breaking other sources
- [ ] Fixture test validates parsing of recorded response
- [ ] Lenient discover run can include Internshala rows in ranked output
- [ ] Rate limiting / polite scraping documented

## Blocked by

- #002 — Hybrid cache replay (no sample fallback by default)
