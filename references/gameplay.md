# Gameplay organization

Use the reference method in `investigacion.md` after vision. Investigate the moment, session and meta loops, progression, rewards, first ten minutes, failure and absence penalties. Focus on player actions and decisions.

Write evidence in `docs/referencias/gameplay.md` and decisions in `docs/design/gameplay.md`:

1. Loop diagram with verbs, decisions and rewards.
2. Systems, dependencies and milestone.
3. Unlock order and rationale.
4. Pacing table: metric, target, event and measurement method.
5. First-ten-minutes walkthrough and onboarding.
6. Failure, absence and punishment rules.
7. M1 prototype cut, M2 vertical slice and deferred systems.

Targets must fit the game. A bot measures timing and rules; it cannot establish human enjoyment or retention. Evaluate M1 with measured behavior and available human feedback, identifying the limits of automation.

For games with spatial traversal or encounters, use [the level design guide](../assets/plantilla/docs/guides/level-design.md) to specify routes, blockouts, pacing and navigation checks. Include procedural reachability and gate-order invariants when maps are generated.
