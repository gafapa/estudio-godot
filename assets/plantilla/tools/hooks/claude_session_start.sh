#!/usr/bin/env bash
# Read-only reminder of persisted studio state; this hook is not a scheduler.
set -u
cd "${CLAUDE_PROJECT_DIR:-$(dirname "${BASH_SOURCE[0]}")/../..}" 2>/dev/null || exit 0
echo '## Studio state'
echo "Branch: $(git branch --show-current 2>/dev/null)"
echo "Latest commit: $(git log -1 --format='%h %s' 2>/dev/null)"
grep -m1 'Current milestone' docs/PLAN.md 2>/dev/null || true
echo 'Open worktrees:'
git worktree list 2>/dev/null || true
echo 'Unmerged feature branches:'
git branch --list 'feat/*' 'fix/*' --no-merged main 2>/dev/null || true
if [ -f docs/DIRECTOR.md ]; then
  awk '/^## Needs the Director|^## Pending decisions/{active=1;print;next} /^## /{active=0} active{print}' docs/DIRECTOR.md
fi
echo 'Resume with /sprint after reading CLAUDE.md and the backlog.'
exit 0
