# PRD: AI Internship Opportunity Intelligence Agent (v1)

**Status:** Ready for agent  
**Triage label:** `ready-for-agent`

---

## Problem Statement

A student or early-career engineer targeting AI, ML, data science, or backend internships in India (and remote-friendly roles) spends hours manually hunting listings across job boards and company sites, reading long descriptions, guessing stipend and PPO likelihood, and tailoring prep without a single view of fit versus their resume.

The existing pipeline prototype discovers internships and generates markdown reports, but live discovery often returns zero ranked results after filtering (missing stipend/duration on international boards), coaching outputs are mostly template placeholders, the CLI has no distinct “explore” versus “apply” workflow, and there is no lightweight UI to review outputs. The product needs a coherent local-first agent (Ollama-only) with hybrid discovery, two-tier filtering, and clear run modes before adding more scrapers.

## Solution

An autonomous **Internship Intelligence Agent** that:

1. **Discovers** internships via live scrapers (Greenhouse, Lever, Wellfound, company career pages), manual URL seeds, optional CSV, and a cached raw dataset when live sources are empty.
2. **Filters and ranks** opportunities against user constraints (role, geo, stipend, duration) with **strict** or **lenient** policies, using PPO only as a ranking signal—not a hard filter.
3. **Matches** the user’s PDF resume to job requirements using skill overlap plus semantic similarity (sentence-transformers by default, optional Ollama embeddings).
4. **Enriches** top listings with JD parsing and company research via **dual Ollama models** (fast for extraction, large for depth).
5. **Produces** markdown reports (top internships, skill gaps, roadmaps, interview prep, application strategy)—templates by default, LLM-rich when requested.
6. **Exposes** two CLI modes—`discover` (weekly exploration) and `shortlist` (apply-ready)—plus a thin Streamlit viewer to browse reports and re-run.

All inference runs **locally through Ollama**; no cloud LLM dependency in v1.

## User Stories

1. As a job seeker, I want to upload my PDF resume, so that the agent can extract skills, projects, and experience automatically.
2. As a job seeker, I want to specify a role query (e.g. “machine learning intern”), so that discovery and filtering focus on relevant titles and descriptions.
3. As a job seeker, I want a minimum stipend threshold in INR, so that low-paying roles are excluded in strict mode or deprioritized in lenient mode.
4. As a job seeker, I want a minimum duration in months, so that short internships are excluded in strict mode or deprioritized when unknown.
5. As a job seeker, I want listings that mention India or Indian cities or remote work, so that I see geographically relevant opportunities.
6. As a job seeker, I want AI/ML/data science/software/backend roles prioritized by keyword matching, so that unrelated postings are dropped early.
7. As a job seeker, I want PPO and full-time conversion signals to affect ranking but never silently hide all listings, so that I can still review roles that do not mention PPO explicitly.
8. As a job seeker, I want live scraping from Greenhouse, Lever, Wellfound, and company career pages, so that I get fresh opportunities without manual copy-paste.
9. As a job seeker, I want to pass manual internship or careers URLs, so that I can seed companies I care about.
10. As a job seeker, I want a text file of seed URLs, so that I can maintain a persistent watchlist.
11. As a job seeker, I want optional CSV input of internships, so that I can rank a curated export from another tool.
12. As a job seeker, I want raw discovered listings saved to a cache file before filtering, so that I can debug why roles were rejected.
13. As a job seeker, I want the pipeline to fall back to cached data when live discovery returns nothing, so that hybrid runs still produce output during scraper outages.
14. As a job seeker, I want a `discover` command with lenient filters by default, so that weekly exploration maximizes visible listings.
15. As a job seeker, I want a `shortlist` command with strict filters by default, so that apply-ready runs only surface high-confidence matches.
16. As a job seeker, I want `--lenient` to allow unknown stipend and duration, so that board postings without parsed INR/months still appear with lower rank.
17. As a job seeker, I want strict mode to reject listings below stipend and duration thresholds when values are known, so that my shortlist is trustworthy.
18. As a job seeker, I want a fit score comparing my resume to each JD, so that I know how competitive I am.
19. As a job seeker, I want a list of matching and missing skills per role, so that I know what to emphasize in applications.
20. As a job seeker, I want semantic similarity between resume and JD text, so that wording overlap beyond keyword lists is captured.
21. As a job seeker, I want `--no-embeddings` for faster runs using lexical similarity only, so that I can iterate without loading embedding models.
22. As a job seeker, I want optional Ollama-based embeddings later, so that I can reduce PyTorch dependency while staying local-only.
23. As a job seeker, I want JD fields extracted (required/preferred skills, tools, responsibilities), so that matching and prep are structured.
24. As a job seeker, I want company research (overview, products, competitors, growth and hiring signals), so that I can prioritize employers intelligently.
25. As a job seeker, I want a composite rank score using stipend, PPO estimate, resume fit, and company quality, so that the top of the list is actionable.
26. As a job seeker, I want configurable `limit` and `top_k`, so that I control cost and report size.
27. As a job seeker, I want skill gap analysis per top role, so that I know exact gaps versus the JD.
28. As a job seeker, I want learning roadmaps (1 week, 2 weeks, 1 month) by default from templates, so that I get quick guidance without waiting on the LLM.
29. As a job seeker, I want interview prep questions by default from templates, so that I have a starting checklist immediately.
30. As a job seeker, I want application strategy (apply now, competitiveness, urgency, rationale) from heuristics, so that I can prioritize applications.
31. As a job seeker, I want `--rich-reports` to use the large Ollama model for coaching sections on top-K roles, so that prep content is detailed when I am serious about applying.
32. As a job seeker, I want five markdown reports written to a reports directory, so that I can read or share them outside the app.
33. As a job seeker, I want the CLI to print paths to generated reports, so that I know where to look after a run.
34. As a job seeker, I want fast Ollama (`qwen2.5:3b`) for JD parsing and optional metadata inference, so that bulk processing stays responsive.
35. As a job seeker, I want large Ollama (`qwen2.5:7b`) for company research and rich coaching, so that deeper text quality is available when needed.
36. As a job seeker, I want `--no-llm` to run heuristics-only when Ollama is down, so that the pipeline degrades gracefully.
37. As a job seeker, I want configurable Ollama base URL and model names, so that I can point at custom local setups.
38. As a job seeker, I want a thin Streamlit app to view the latest reports, so that I do not open markdown files manually.
39. As a job seeker, I want to trigger discover or shortlist from Streamlit, so that I can re-run without memorizing CLI flags.
40. As a job seeker, I want logging of per-listing filter accept/reject reasons, so that I understand empty result sets.
41. As a job seeker, I want deduplication by title, company, and apply URL, so that the same role from multiple sources appears once.
42. As a job seeker, I want `--live` to disable sample fallback data, so that I can force real discovery only when debugging scrapers.
43. As a maintainer, I want Internshala scraping added after pipeline fixes, so that India-native stipend and duration appear more often in live data.
44. As a maintainer, I want expanded Greenhouse/Lever board seeds, so that hybrid discovery improves without fragile general job boards.
45. As a maintainer, I want Gemini, ChromaDB, jobspy, and full Streamlit product UI out of v1 scope, so that the agent ships with a narrow, testable surface.

## Implementation Decisions

### Run profiles (deep module: `RunProfile`)

Introduce two first-class CLI subcommands—`discover` and `shortlist`—each mapping to a frozen preset of `AgentSettings`:

| Setting | `discover` | `shortlist` |
|---------|------------|-------------|
| Filter mode | lenient | strict |
| Rich reports | off | on |
| Typical limit / top_k | 30 / 10 | 30 / 5 |
| Embeddings | on | on |
| PPO hard filter | off | off |

The existing single entrypoint remains composable: subcommands set defaults; explicit flags override.

### Filter policy (deep module: `FilterPolicy`)

Encapsulate stipend, duration, role query, role keywords, geo (India + remote-global), and optional PPO hard filter (disabled in v1 product defaults).

- **Strict:** reject when `stipend_inr` or `duration_months` are known and below thresholds; reject when known values are zero if treated as “known missing” (product choice: zero means unknown in lenient, reject in strict only when explicitly parsed as below threshold—document in module).
- **Lenient:** pass when stipend or duration is zero/unknown; apply rank penalty downstream via stipend score component.

Interface shape:

```
FilterPolicy(mode: strict | lenient, thresholds...) -> (accepted: bool, reason: str, penalties: dict)
```

### Hybrid discovery orchestrator (extend `InternshipRepository` / scraper)

Discovery order unchanged in spirit: manual URLs → live sources → save raw cache → filter.

Add explicit **cache replay** step: if filtered live set is empty and not `--live`, load last raw cache from `data/internships.json` and re-filter (lenient or strict per run profile).

Remove or gate **sample fallback** behind dev-only flag; hybrid mode prefers real cache over fabricated samples.

### Dual Ollama routing (deep module: `OllamaRouter`)

Replace single `OllamaClient` injection with a router exposing:

- `fast` → `qwen2.5:3b` for `JDParser`, optional stipend/duration inference
- `large` → `qwen2.5:7b` for `CompanyResearcher`, rich coaching generators

`JDParser` and `CompanyResearcher` receive the appropriate client; coaching generators gain an optional LLM path when `rich_reports=True`.

### Coaching generation (deep module: `CoachingGenerator`)

Facade over skill gaps (rule-based), roadmaps, interview prep, application strategy:

- **Template mode** (default): current deterministic generators.
- **Rich mode:** large model prompts per `RankedInternship`, capped at `top_k`.

Skill gap analysis stays rule-based in v1 (feeds both modes).

### Resume match engine (extend `ResumeMatcher`)

Keep 60/40 skill/semantic blend.

- Default: sentence-transformers `all-MiniLM-L6-v2`.
- `--no-embeddings`: Jaccard fallback (existing).
- Future hook: `--ollama-embeddings` with model name in settings (interface only in v1 if not implemented).

### Ranking engine

Keep weighted formula: 25% stipend, 25% PPO score, 35% fit, 15% company quality. In lenient mode, missing stipend contributes 0 to stipend component rather than excluding the row.

### Report generator

Continue writing five markdown files under configurable `reports_dir`. Optionally namespace by run id or timestamp in a follow-up; v1 may keep flat layout.

### Streamlit viewer (thin app)

Read-only browsing of latest reports plus forms to invoke `discover` / `shortlist` subprocess or in-process agent run with resume path and role query. No upload persistence beyond `uploads/` convention.

### Configuration

Extend `AgentSettings` with: `filter_mode`, `rich_reports`, `ollama_fast_model`, `ollama_large_model`, `use_ollama_embeddings` (optional).

### Scraper roadmap (sequenced, not all v1)

1. Pipeline + lenient + cache replay (E)
2. Internshala scraper (A)
3. Expanded board seed lists (D)

### Domain models

Retain existing dataclasses: `Internship`, `ResumeProfile`, `JDProfile`, `MatchResult`, `RankedInternship`, `SkillGapPlan`, `LearningRoadmap`, `InterviewPrep`, `ApplicationStrategy`, `PPOPrediction`, `CompanyResearch`.

## Testing Decisions

**Principle:** Test observable behavior through public interfaces—filter decisions, rank ordering, discovery fallback, report file existence—not private methods or LLM verbatim output.

**Modules to test (recommended):**

| Module | What to test |
|--------|----------------|
| `FilterPolicy` | Strict vs lenient accept/reject matrix for stipend/duration zero, known below threshold, role/geo keywords |
| `InternshipScraper` / discovery | Dedupe keys; cache save/load; fallback to cache when live filtered empty; manual URL routing by host |
| `RankingEngine` | Score ordering given fixed inputs; stipend penalty when zero in lenient |
| `ResumeMatcher` | Fit score monotonicity when more skills match; `--no-embeddings` path produces stable lexical score |
| `RunProfile` | `discover` vs `shortlist` preset maps to expected settings |
| `ReportGenerator` | `write_all` creates five non-empty files when given non-empty ranked list |

**Modules not unit-tested in v1:** Ollama HTTP calls (mock `OllamaClient` / router); Streamlit UI (manual smoke test).

**Prior art:** No project tests exist today; introduce `tests/` with pytest, following arrange-act-assert and fixture JSON for sample internships.

## Out of Scope

- Cloud LLM providers (Gemini, OpenAI, LiteLLM product integration)
- ChromaDB vector store and RAG over historical JDs
- LinkedIn, Indeed, Naukri, and jobspy-based scrapers in v1
- Full Streamlit product (upload wizard, in-app discovery management)
- Hard PPO-required filtering as default (explicitly rejected; PPO is rank-only)
- Geo tightening to India-only without “remote” (current India + remote-global retained)
- Production deployment, auth, multi-user state
- Removing `venv` / `litellm-env` from workspace (housekeeping, not feature)
- CI/CD and published package distribution

## Further Notes

- Original `RESEARCH_AGENT.md` spec diverges on Gemini, ChromaDB, PPO-required, and full job-board coverage; this PRD reflects **grilled** product decisions (local Ollama, hybrid discovery, two-tier filters, PPO as signal, tiered coaching, CLI + thin Streamlit).
- Many existing `reports/` directories contain stub markdown (headers only), consistent with empty post-filter ranked lists; v1 should acceptance-test that `discover --lenient` with cache produces non-empty `top_internships.md`.
- Default Ollama models: fast `qwen2.5:3b`, large `qwen2.5:7b`; override via CLI flags.
- Issue tracker publish: apply label `ready-for-agent` when creating the tracking issue.
