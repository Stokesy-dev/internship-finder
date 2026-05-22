# Issue 004: Dual Ollama model routing (fast vs large)

**Labels:** `ready-for-agent`  
**Type:** AFK  
**Blocked by:** #003

## Parent

[PRD: AI Internship Intelligence Agent v1](../PRD-internship-intelligence-v1.md)

## What to build

Replace single-model Ollama injection with an `OllamaRouter` (or equivalent) exposing:

- **Fast** client — default `qwen2.5:3b` — for JD parsing (and optional future metadata inference)
- **Large** client — default `qwen2.5:7b` — for company research

Extend `AgentSettings` with `ollama_fast_model`, `ollama_large_model`, and base URL. Wire `JDParser` to fast and `CompanyResearcher` to large. Preserve `--no-llm` heuristic fallback.

Mock Ollama HTTP in tests; verify correct model id per call site.

## Acceptance criteria

- [ ] JD parsing uses fast model by default
- [ ] Company research uses large model by default
- [ ] CLI flags can override fast/large model names and Ollama URL
- [ ] `--no-llm` skips LLM calls with existing heuristic behavior
- [ ] Tests mock router and assert model selection per consumer
- [ ] Shortlist/discover pipeline completes with Ollama available and produces enriched ranked rows

## Blocked by

- #003 — `discover` and `shortlist` CLI run profiles
