---
name: hito
description: "Review milestone criteria with build, gameplay, visual and platform evidence before deciding the next milestone."
---

# Hito

All documentation, code identifiers, comments and docstrings must be in English. Follow CLAUDE.md, docs/AGENTES.md and the Director's scope and operating mode.

Read PLAN criteria and gather independent evidence at an immutable integrated SHA: full CI, inspected captures, available Android hardware, playtest personas and implemented balance tooling where relevant. Do not require nonexistent tools or mark unavailable checks passed. Run global design, art and gameplay reviews within capacity.

Write docs/hitos/<MILESTONE>.md with criterion/evidence/status table, debt, deferred scope, limitations, pacing results and a short Director play guide. A blocker or failed machine gate prevents approval. Automatic mode records continue/iterate/reduce/pivot/stop with evidence; gated mode waits. Update PLAN/DIRECTOR and publish next tickets. Prepare M5 artifacts locally; publication requires existing or newly obtained authorization.

Include tools/workflow_metrics.py report in the retrospective, comparing similar ticket classes and escaped defect severity/count. Identify missing measurements and avoid equating summed worker durations with delivery wall time. Preserve full exports and platform checks regardless of quick-CI cache reuse.
