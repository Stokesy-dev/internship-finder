# Issue 005: Rich LLM coaching reports (`--rich-reports`)

**Labels:** `ready-for-agent`  
**Type:** AFK  
**Blocked by:** #004

## Parent

[PRD: AI Internship Intelligence Agent v1](../PRD-internship-intelligence-v1.md)

## What to build

Add a `CoachingGenerator` facade (or extend pipeline) so **template** roadmaps, interview prep, and application strategy remain the default, while **rich** mode uses the **large** Ollama model to generate substantive coaching content for top-K ranked internships.

`shortlist` preset enables rich reports; `discover` keeps templates only. Skill gap analysis stays rule-based in both modes.

Mock LLM responses in tests; verify markdown report sections contain generated content (not headers only) when rich mode is on.

## Acceptance criteria

- [ ] `discover` writes template-based coaching sections
- [ ] `shortlist` (or `--rich-reports`) invokes large model for top-K coaching
- [ ] `learning_roadmaps.md`, `interview_prep.md`, `application_strategy.md` have real content in rich mode
- [ ] Rich mode degrades gracefully when Ollama fails (fallback or clear error)
- [ ] Tests mock LLM and assert rich vs template paths
- [ ] Skill gaps remain rule-based in both modes

## Blocked by

- #004 — Dual Ollama model routing (fast vs large)
