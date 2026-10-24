# Production loop

Use role separation, immutable commit validation and explicit evidence. Independent review is a second examination, not a guarantee. Bot metrics do not establish human enjoyment.

## Milestones

| Milestone | Question | Evidence |
|---|---|---|
| M0 foundations | Does the harness work? | Full verification, exports, PC smoke, captures, telemetry and bot; hardware checks where available |
| M1 prototype | Is the core mechanic worth developing? | Small playable loop, pacing measurements and available human feedback |
| M2 vertical slice | Can we produce final quality? | Representative UI, art, audio, saves and performance |
| M3 alpha | Is the whole game playable? | Intended systems and complete end-to-end path |
| M4 beta | Is it ready for release qualification? | Content complete, no blockers, accessibility, balance and platform evidence |
| M5 launch | Can the qualified build reach players? | Reviewed artifacts, store material, licenses and authorized publication |

Project skills: `investigar` researches, `spec` designs/contracts, `sprint` delivers, `playtest` analyzes feedback, `hito` reviews milestones. IDs remain stable for compatibility.

## Work and review

The canonical ownership and review matrix is `docs/AGENTES.md`. Rigor changes design documentation and adversarial testing, not basic machine/QA checks.

Use [fast delivery](../assets/plantilla/docs/guides/fast-delivery.md): group coherent small edits, let concise tickets specify small changes, use focused tests while implementing and reuse only matching successful machine evidence. A qualified non-author reviewer may combine low/medium-risk review responsibilities; high-risk work retains separate QA/technical review. Start separate reviews concurrently where capacity and runtime locks permit.

Keep up to `ESTUDIO_WIP` independent implementation tickets active, bounded by agent capacity. Reserve review capacity. Launch disjoint zones; integrate sequentially. Reviewers receive ticket, spec and SHA without author conclusions. New commits invalidate approvals for changed criteria.

After three failed review iterations, record disagreement and narrow, redesign or block the ticket. Never waive failed machine gates or unresolved blockers as debt. Silence is not approval.

## Decisions and stopping

Automatic mode chooses reversible options within scope using pillars, references and evidence. Record alternatives, rationale and reversal. Gated mode waits at creative and milestone decisions. Existing authorization persists; stop dependent work when spending, publication or destruction lacks authorization, and continue independent work.

At M1, choose continue, iterate, pivot or stop. After two unsuccessful pacing iterations reconsider the mechanic instead of endlessly adjusting constants. Make scope cuts explicit; do not relabel failed criteria as passed.

## Rigor and resumption

Light: concise specs and design review only for pillar changes. Standard: design review for new systems. Full: ADRs for critical changes and adversarial tests. High-risk tickets always receive adversarial tests. Code/visual/gameplay review follows the canonical matrix.

Persist milestones, tickets, SHAs, evidence, decisions and next action. Inspect branches/worktrees on resumption. SessionStart displays state; it does not schedule sessions. Use scheduling only through a real available feature requested by the user.

Write a short retrospective per milestone. Prepare release/maintenance material locally, distinguish simulation from platform qualification, and obtain missing publication authorization when artifacts are ready.

Use local workflow metrics to compare implementation, validation, review and waiting time alongside escaped defects. Run fresh complete test CI on integrated SHAs; keep milestone exports and qualification evidence. Configuration changes alone do not establish a speedup or unchanged quality.
