# Issue 001: Lenient filters + rank penalty for unknown stipend/duration

**Labels:** `ready-for-agent`  
**Type:** AFK  
**Blocked by:** None — start here

## Parent

[PRD: AI Internship Intelligence Agent v1](../PRD-internship-intelligence-v1.md)

## What to build

Introduce a `FilterPolicy` module with **strict** and **lenient** modes that encapsulates stipend, duration, role query, target role keywords, and India/remote-global geo rules. Wire it into the internship discovery filter path so lenient mode **passes** listings with zero/unknown stipend or duration instead of rejecting them.

Adjust the ranking engine so unknown/zero stipend in lenient mode **lowers** the stipend component of the composite score rather than relying on pre-filter exclusion alone.

Ensure PPO remains **rank-only** (never a default hard filter).

Add pytest coverage for the policy decision matrix and rank ordering with zero stipend.

End-to-end outcome: a CLI run with `--lenient` against cached or fixture internship data produces **non-empty** markdown reports (especially `top_internships.md` with ranked rows).

## Acceptance criteria

- [ ] `FilterPolicy` exposes strict/lenient with clear accept/reject reasons per listing
- [ ] Lenient mode allows `stipend_inr=0` and `duration_months=0` when otherwise eligible (role, geo)
- [ ] Strict mode rejects known-below-threshold stipend and duration
- [ ] Ranking penalizes missing stipend in lenient mode (lower stipend score component, not exclusion)
- [ ] PPO is not required by default; `--ppo-required` remains opt-in only
- [ ] Unit tests cover strict vs lenient matrix and rank ordering with zero stipend
- [ ] `python main.py --resume <pdf> --lenient` (with cache or CSV) writes five reports with substantive top-internships content

## Blocked by

None - can start immediately
