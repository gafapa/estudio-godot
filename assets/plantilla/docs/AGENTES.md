# Studio roles and delivery policy

Canonical ownership, review and ticket contract. Documentation, identifiers and comments are English. Role IDs and legacy file paths remain stable for compatibility.

## Roles and ownership

For Codex model and reasoning assignments, use [the model routing guide](guides/codex-models.md) and `.codex/agents/*.toml`. Claude Code profiles remain in `.claude/agents/`. Model selection does not alter ownership, permissions or required evidence.

| Role | Owned work |
|---|---|
| Producer (main session) | Vision, plan, backlog, Director inbox, integration and decisions |
| investigador-juegos | Reference research in docs/referencias/ |
| disenador-juego | Specs in docs/design/ and limited example content |
| arquitecto | docs/contracts/, src/game/contracts/, fixtures, contract tests and ADRs |
| ingeniero-gameplay | src/sim/, src/game/ except contracts and assigned launcher files; unit tests |
| ingeniero-ui | src/ui/, UI tests and assigned translation files |
| artista-tecnico | src/world/, shaders/, visual assets and visual tests |
| disenador-sonido | src/audio/, assets/audio/, audio tests and assigned bus layout |
| disenador-contenido | Assigned data/content/ batches and translation files |
| analista-balance | data/balance/, tools/balance/, tools/balance.sh and reports |
| ingeniero-plataforma | tools/, addons/, export_presets.cfg, excluding explicit ticket reservations |
| qa-tester | Integration, visual and soak tests, bot and reproducible reports |
| revisor-codigo | Technical review; no production edits |
| revisor-diseno | Design review reports |
| director-arte | Visual review reports |
| revisor-jugabilidad | Gameplay review reports |
| playtester | Bot sessions, telemetry analysis and playtest reports |
| responsable-lanzamiento | Release material and feedback; publication requires authorization |

Ticket Allowed paths restrict role ownership. Shared licenses, translations and project settings need explicit assignment or serialized integration. Do not launch overlapping patterns. The Architect writes/updates contracts; the Producer approves/integrates them.

## Specialized production guides

Read only guides relevant to the ticket:

- [Level design](guides/level-design.md): the game designer specifies spatial intent; explicitly assigned gameplay engineers or technical artists implement the blockout and scenes. Content designers retain their assigned data-only scope.
- [Technical art](guides/technical-art.md): technical artists coordinate asset/import budgets with the platform engineer and measure representative load.
- [Audio](guides/audio.md): the sound designer specifies routing, concurrency, mixing and lifecycle behavior with the existing gameplay contracts.

QA checks affected criteria using these guides. Shared budgets and design documents still require explicit Allowed paths; consulting a guide grants no additional ownership. Missing human, listening or target-hardware evidence remains pending.

All engine work follows [quiet Godot testing](guides/quiet-godot-tests.md): prefer headless, close and verify owned processes after every invocation, release the machine lease and yield five seconds for other applications. Respect active unrelated engines and never terminate them. Review concurrency does not authorize overlapping engine runs.

## Definition of Ready

A ticket has objective, context, owner, milestone, risk, dependencies, disjoint Allowed paths and observable criteria. Integrate shared contracts/fixtures before consumers. Architects and reviewers doing work requiring a gate need a ticket and explicit paths too.

Group coherent small edits with one owner and verification outcome; keep critical systems and unrelated work separate. For a small change to an approved system, the ticket can be its specification. Documentation and ADR depth follow the actual decision, not a fixed document count. See [fast delivery](guides/fast-delivery.md).

## Quality gates

| Level | Low risk | Medium risk | High risk |
|---|---|---|---|
| N0 immutable commit: zone, lint, data, nonempty tests | Required | Required | Required |
| N1 independent QA with its own evidence | Required | Required | Required |
| N2 code review | Optional | Required | Required |
| N2 art review | Required when visible | Required when visible | Required when visible |
| N2 gameplay review | Required when playable | Required when playable | Required when playable |
| N3 adversarial tests | Optional | Required with full rigor | Required |

High risk: saves, contracts, determinism, economy and shared foundations. Medium: player-visible behavior. Low: internal tools or isolated content without meaningful player effects. Use medium when uncertain. Rigor does not weaken this matrix: light uses concise specs and design review only for pillar changes; standard reviews new systems; full adds ADRs and adversarial cases for critical work.

For low/medium risk, one qualified reviewer independent of the author may fulfill N1 and applicable N2 responsibilities, with separate criterion results and verdicts. Use specialists when expertise is missing. High-risk tickets retain separate QA and technical reviewers plus applicable specialist/adversarial checks. Launch separate reviews concurrently when capacity, isolated outputs and Godot/device locks permit.

N0 may reuse a matching successful quick-CI receipt under the fast delivery guide; zone checks always rerun. Reviewers still gather independent scenario and inspection evidence. Use fresh execution for high-risk delivery and suspected flaky/external-state changes. Full CI and human/device qualification are not cached.

Never waive a machine failure or blocking review as debt. Minor approved notes become tickets. After three failed review iterations narrow, redesign or block the ticket. New commits invalidate approval for changed criteria. Reviewers receive ticket, spec and SHA, not author conclusions.

Integrate sequentially, validate the merge commit with `bash tools/ci.sh --quick --commit <merge-SHA> --fresh` (complete test suite, no exports) and inspect affected screenshots. Revert failed integration without deleting the author's branch. Mark INTEGRATED only after checks pass.

## Ticket format

```markdown
### M1-01 - Short title
- **Role:** ingeniero-gameplay
- **Milestone:** M1
- **Risk:** medium
- **Depends on:** M0-02
- **Origin:** spec / Director / PT-001#1
- **Status:** READY | IN_PROGRESS (branch) | INTEGRATED SHA | RETURNED | BLOCKED
- **Objective:** Observable outcome
- **Context:** Spec, contract, fixtures and references
- **Allowed paths:** `src/sim/example/**`, `tests/unit/sim/example/**`
- **Acceptance criteria:**
  - [ ] Behavior and verification method
- **Out of scope:** Explicit exclusions
```

Patterns are relative POSIX globs: * stays within a component; ** crosses directories. Validate both sides of renames and deletions. No ignored-path exemption.

## Delivery and review

Delivery reports identify ticket, SHA, files, criteria evidence, limitations and proposals outside the zone. Keep summaries short; store logs and PNGs in files. Every review ends with VERDICT: APPROVED, VERDICT: APPROVED_WITH_NOTES or VERDICT: CHANGES_REQUIRED.

## Milestones and resumption

Use docs/PLAN.md. Automatic mode chooses continue, iterate, reduce scope, pivot or stop with evidence in docs/DIRECTOR.md; gated mode waits. Missing hardware evidence is pending, never passed. Honor existing authorization. SessionStart displays saved state; it does not schedule future sessions.
