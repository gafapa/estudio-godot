---
name: playtest
description: "Run available seeded bot personas and turn measured gameplay findings into scoped feedback tickets."
---

# Playtest

All documentation, code identifiers, comments and docstrings must be in English. Follow CLAUDE.md, docs/AGENTES.md and the Director's scope and operating mode.

Require a validated integrated commit and tools/playtest.sh; if absent, record the prerequisite instead of pretending to run it. Choose personas from data/playtest/personas.json and the assigned duration/seeds. Assign playtester, using isolated output directories per session/persona. Inspect telemetry and screenshot sequences against gameplay pacing goals.

Write docs/playtests/PT-NNN.md. Convert bugs to reproducible tickets; pacing issues to balance/rule proposals; clarity issues to UX work; creative preferences to Director decisions according to mode. Record origin PT-NNN#k and verify fixes in a subsequent playtest. State that bots cannot establish enjoyment, physical touch feel or retention.
