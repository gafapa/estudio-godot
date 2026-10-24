---
name: spec
description: "Turn a feature or feedback into a reviewed design, contracts and ready implementation tickets."
---

# Spec

All documentation, code identifiers, comments and docstrings must be in English. Follow CLAUDE.md, docs/AGENTES.md and the Director's scope and operating mode.

Read vision, gameplay, UX, character designs, milestone and feedback. Research missing evidence, then assign disenador-juego a concise spec with observable criteria. Request a clean design review as required by rigor. Iterate at most twice before recording the disagreement and narrowing/redesigning; do not mark blockers approved.

For small changes to an approved system, use a concise ticket as the spec instead of creating extra documents or agent handoffs. Group coherent small edits with one owner and verification outcome, preserving critical-system boundaries. Read docs/guides/fast-delivery.md; new systems and critical decisions retain required design review, contracts and ADRs.

The Architect writes contracts, deterministic fixtures, tests and ADRs and proposes disjoint tickets. Give contract work its own ticket/Allowed paths and gate/reviews. The Producer approves and integrates contracts before consumer tickets become READY. For a single-module change, the Producer can write tickets directly. Update docs/backlog/ with risk, dependencies and criteria. Record creative decisions according to operating mode.
