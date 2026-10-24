# Godot 4 architecture

Adapt architecture to the game rather than forcing every genre into a management simulation.

- Keep rules, inventory, progression, economy and saves independent of presentation where practical. Real-time movement and physics may live in nodes.
- UI and world send validated commands and read state or ViewModels; avoid hidden mutation from render code.
- Seed randomness per subsystem. Inject time for tests and accelerated simulation. Record seeds and commands for reproduction.
- Store balance values in schema-validated data. Version saves with migrations and historical fixtures.
- The Architect writes contracts, fixtures and ADRs; the Producer approves and integrates them before dependent tickets. Consumers request boundary changes.
- Use typed GDScript and translation keys for game text. Documentation, identifiers, comments and docstrings are English.
- Development telemetry is local and disabled in release unless the Director requests a documented production design.

## Genre choices

| Genre | Additional concerns |
|---|---|
| Management/idle | Bounded offline progress, fake clock, accelerated simulation |
| Collection/random rewards | Visible probabilities, statistical validation, avoid exploitative defaults |
| Action/platformer | Physics nodes, frame budget, input buffering and game feel |
| Turn-based/puzzle | Undo policy, deterministic resolution, solvable content |
| Narrative | Story variables, dialogue data, branch coverage |
| Multiplayer | Authority, protocol versions and reconciliation; ADR first |
| Mobile | Current resolution, safe areas, thermal and memory budgets |

## Engine checks

Consult the installed API (`tools/dump_api.sh`) for uncertain signatures. Reimport after adding global classes. Use Godot 4 syntax. Avoid method names colliding with global helpers and test determinism.

Headless runs do not validate rendering. Use `tools/screenshot.sh` and inspect PNGs. Separate outputs and user directories per worktree. Use `tools/ci.sh --isolated` or commit validation to avoid the Director's editor. Set `GODOT_REAL` for direct guarded invocations and `GODOT` for high-level tools.

Keep scenes small with one owner. Use LF in shell files. Record engine limitations with reproducible examples rather than unverified universal rules.
