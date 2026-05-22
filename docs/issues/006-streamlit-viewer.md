# Issue 006: Thin Streamlit report viewer + re-run triggers

**Labels:** `ready-for-agent`  
**Type:** AFK  
**Blocked by:** #003

## Parent

[PRD: AI Internship Intelligence Agent v1](../PRD-internship-intelligence-v1.md)

## What to build

Ship a minimal Streamlit app that:

1. Displays the five latest markdown reports from the configured reports directory
2. Provides a form to trigger `discover` or `shortlist` with resume path and role query (subprocess or in-process agent run)
3. Shows run status / errors surfaced to the user

No full product UI (upload wizard, auth, discovery management). Manual smoke test is sufficient; no browser automation required.

## Acceptance criteria

- [ ] `streamlit run <app>` starts without import errors
- [ ] All five report types render when present under `reports/`
- [ ] User can launch discover or shortlist from the UI
- [ ] Resume path defaults to `uploads/` convention; role query optional
- [ ] Failed runs show actionable error message
- [ ] README or docs note how to start the viewer

## Blocked by

- #003 — `discover` and `shortlist` CLI run profiles
