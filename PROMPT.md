# Ralph agent prompt (one task per run)

You are implementing **one** GitHub issue for the Internship Intelligence Agent.

## Read first

1. `@.ralph/current-issue.md` — the issue you must complete this run
2. `@progress.txt` — what was already done (append only; never rewrite history)
3. `@docs/PRD-internship-intelligence-v1.md` — product context

## Rules

1. Implement **only** the current issue. Do not start the next issue.
2. Meet every acceptance criterion in the issue body.
3. Add or update **pytest** tests for behavior you change.
4. Run tests before committing; fix failures.
5. **Commit** with a message like: `feat: <short description> (closes #N)` or `feat(#N): ...`
6. **Append** to `progress.txt` (do not delete prior entries):

   ```
   ## <date> — Issue #N — <title>
   - <bullets>
   - Tests: <command> — pass/fail
   - Commit: <hash>
   ```

7. If the issue is fully done, comment on the GitHub issue with a short summary (use `gh issue comment` if available).

## Do not

- Refactor unrelated code
- Add Gemini, ChromaDB, or new scrapers unless the issue says so
- Enable PPO as a default hard filter

When finished, stop. Do not pick another task.
