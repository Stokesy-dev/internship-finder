#!/usr/bin/env bash
# Human-in-the-loop Ralph — one agent pass per run.
# https://www.aihero.dev/getting-started-with-ralph
#
# Usage:
#   ./ralph-once.sh           # next open issue labeled ready-for-agent
#   ./ralph-once.sh 1         # specific issue number
#   ./ralph-once.sh --print   # write prompt files only (run agent in Cursor manually)

set -euo pipefail

REPO="${GITHUB_REPO:-Stokesy-dev/internship-finder}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

RALPH_DIR="$ROOT/.ralph"
ISSUE_FILE="$RALPH_DIR/current-issue.md"
PRINT_ONLY=false
ISSUE_NUM=""

for arg in "$@"; do
  case "$arg" in
    --print) PRINT_ONLY=true ;;
    -h|--help)
      sed -n '3,8p' "$0"
      exit 0
      ;;
    *)
      if [[ "$arg" =~ ^[0-9]+$ ]]; then
        ISSUE_NUM="$arg"
      fi
      ;;
  esac
done

mkdir -p "$RALPH_DIR"

if [[ -z "$ISSUE_NUM" ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "error: gh CLI not found. Install GitHub CLI or pass an issue number: ./ralph-once.sh 1" >&2
    exit 1
  fi
  ISSUE_NUM="$(gh issue list --repo "$REPO" --label "ready-for-agent" --state open --json number --jq 'min_by(.number) | .number' 2>/dev/null || true)"
  if [[ -z "$ISSUE_NUM" || "$ISSUE_NUM" == "null" ]]; then
    echo "error: no open issues with label ready-for-agent in $REPO" >&2
    exit 1
  fi
  echo "→ Next issue: #$ISSUE_NUM ($REPO)"
fi

if command -v gh >/dev/null 2>&1; then
  gh issue view "$ISSUE_NUM" --repo "$REPO" --json title,body,number,url \
    | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f\"# Issue #{d['number']}: {d['title']}\n\")
print(f\"**URL:** {d['url']}\n\")
print(d['body'])
" > "$ISSUE_FILE"
else
  echo "error: gh required to fetch issue #$ISSUE_NUM" >&2
  exit 1
fi

echo "$ISSUE_NUM" > "$RALPH_DIR/current-issue-number.txt"

if $PRINT_ONLY; then
  echo "Wrote $ISSUE_FILE"
  echo ""
  echo "In Cursor Agent, run with context:"
  echo "  @.ralph/current-issue.md @progress.txt @docs/PRD-internship-intelligence-v1.md @PROMPT.md"
  echo ""
  echo "Or paste PROMPT.md instructions after attaching those files."
  exit 0
fi

# Build a single prompt string for CLIs that accept inline prompts
AGENT_PROMPT="$(cat "$ROOT/PROMPT.md")

---
CURRENT ISSUE FILE: .ralph/current-issue.md
ISSUE NUMBER: #$ISSUE_NUM
"

run_claude() {
  if ! command -v claude >/dev/null 2>&1; then
    return 1
  fi
  claude --permission-mode acceptEdits \
    "@$ISSUE_FILE" "@$ROOT/progress.txt" "@$ROOT/docs/PRD-internship-intelligence-v1.md" \
    "$AGENT_PROMPT"
}

run_cursor_agent() {
  if ! command -v cursor >/dev/null 2>&1; then
    return 1
  fi
  # Cursor CLI agent mode (if available in your install)
  cursor agent -p "$AGENT_PROMPT" --workspace "$ROOT" 2>/dev/null && return 0
  return 1
}

if run_claude; then
  echo "✓ Claude run finished for issue #$ISSUE_NUM"
  exit 0
fi

if run_cursor_agent; then
  echo "✓ Cursor agent run finished for issue #$ISSUE_NUM"
  exit 0
fi

# Fallback: Cursor IDE — human runs agent with @-mentions
echo "No non-interactive agent CLI found (tried: claude, cursor agent)."
echo ""
echo "Run in Cursor Agent (recommended):"
echo "  1. Open: .ralph/current-issue.md (issue #$ISSUE_NUM)"
echo "  2. Attach: @.ralph/current-issue.md @progress.txt @docs/PRD-internship-intelligence-v1.md @PROMPT.md"
echo "  3. Send the PROMPT.md instructions"
echo ""
echo "Or preview only next time: ./ralph-once.sh --print $ISSUE_NUM"
exit 0
