# Godot studio for Codex

Read `CLAUDE.md` for the shared project rules, architecture, commands and environment; its filename is retained for compatibility. Apply `docs/AGENTES.md` for ownership, tickets and reviews. Documentation, code identifiers and comments must be in English.

Project-scoped Codex agents live in `.codex/agents/*.toml`. Each specifies its model, reasoning effort and complete role instructions. Read `docs/guides/codex-models.md` when assigning or adjusting roles. Keep the main session's existing model unless the user requests a change.

When supported and authorized, delegate ready tickets to the matching named agent with disjoint ownership and an independent review assignment. If the host exposes explicit model/effort overrides instead of named agents, use the role's TOML settings and instructions. Use a fresh role context containing the ticket, contracts and exact SHA; do not pass author conclusions to reviewers. Verify the effective model where the host exposes it. If model selection or delegation is unavailable, report that limitation and follow the sequential fallback in the shared rules.

The shared workflow procedures remain in `.claude/skills/`: read `investigar/SKILL.md` for research, `spec/SKILL.md` for design, `sprint/SKILL.md` for delivery, `playtest/SKILL.md` for playtests and `hito/SKILL.md` for milestone review when needed. These paths are references, not a claim that Codex discovers Claude skills or executes Claude hooks automatically. Inspect saved plan/backlog state on resumption and run the documented checks explicitly.
