---
name: sprint
description: "Resume and deliver scoped game tickets with isolated commit validation, risk-based review and sequential integration."
---

# Sprint

All documentation, code identifiers, comments and docstrings must be in English. Follow CLAUDE.md, docs/AGENTES.md and the Director's scope and operating mode.

Read PLAN, backlog, DIRECTOR, latest playtest/retro, branches and worktrees. Resume existing branches before relaunching work. Follow the canonical ownership and quality matrix in docs/AGENTES.md.

Read docs/guides/fast-delivery.md. Group only coherent small edits with shared ownership and acceptance evidence; concise tickets can specify changes to approved systems. During implementation use tools/dev_check.sh with relevant tests, broadening for shared dependencies or failures. Delivery still requires complete immutable test CI. Reuse matching successful machine receipts, never independent review conclusions.

Start READY tickets with satisfied dependencies and disjoint Allowed paths, up to available capacity/ESTUDIO_WIP. Reserve review capacity. Give each implementation agent a worktree, complete ticket, spec/contracts and branch. Persist IN_PROGRESS. When delegation is unavailable work sequentially and record the review limitation.

Each delivery identifies its committed SHA. Run tools/gate.sh on that SHA. Reviewers receive ticket/spec/SHA without author conclusions and gather their own evidence. New commits invalidate affected approvals. After three failed reviews narrow/redesign/block; never waive machine failures or blockers as debt.

For low/medium risk, assign one qualified non-author reviewer to QA and applicable N2 responsibilities with separate criterion results. High-risk work keeps separate QA/technical review and adversarial checks. Run separate reviews concurrently with isolated outputs and runtime locks where capacity permits. Reviewers reproduce scenarios and inspect the SHA independently even when machine evidence is reused. High-risk delivery uses validate_commit.py with --ticket, --quick and --fresh.

Integrate approved SHAs one at a time; validate the resulting merge commit using tools/ci.sh --quick --commit <merge-SHA> --fresh, and inspect affected captures in isolation. Revert failed integration; retain author branches. Mark INTEGRATED only after evidence passes. Push only within existing authorization and after checking the actual remote.

Validation timings are recorded automatically. Record measured implementation, review, waiting and integration durations with tools/workflow_metrics.py, plus unique defects discovered after integration. Include the report in milestone retrospectives; summed worker time is not wall-clock time.

Maintain design one step ahead and playtest integrated gameplay when tools exist. Report Director decisions, what to play, evidence and limitations after a small batch. Continue ready work within scope; run hito on milestone completion. Stop when requested, when all work is blocked, or before an unauthorized external/destructive action. Persist the next action; do not promise continuation across closed sessions.
