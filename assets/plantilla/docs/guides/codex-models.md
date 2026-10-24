# Codex role models

These project defaults balance reasoning depth with focused execution. They are routing choices, not benchmark results. Model identifiers and effort settings were checked against official documentation and the local model catalog on 2026-10-21; account and client availability can differ.

| Role | Model | Reasoning effort |
|---|---|---|
| arquitecto | gpt-6.1-sol | medium |
| disenador-juego | gpt-6.1-sol | medium |
| ingeniero-gameplay | gpt-6.1-sol | medium |
| ingeniero-ui | gpt-6.1-sol | medium |
| artista-tecnico | gpt-6.1-sol | medium |
| ingeniero-plataforma | gpt-6.1-sol | medium |
| revisor-codigo | gpt-6.1-sol | medium |
| revisor-diseno | gpt-6.1-sol | medium |
| director-arte | gpt-6.1-sol | medium |
| revisor-jugabilidad | gpt-6.1-sol | medium |
| qa-tester | gpt-6.1-sol | medium |
| analista-balance | gpt-6.1-sol | medium |
| disenador-sonido | gpt-6.1-sol | medium |
| investigador-juegos | gpt-6-luna | medium |
| disenador-contenido | gpt-6-luna | low |
| playtester | gpt-6-luna | low |
| responsable-lanzamiento | gpt-6-luna | low |

Sol handles shared architecture, implementation, visual judgment, balance analysis and independent review; these roles use medium reasoning. Bounded research also uses medium; routine content batches, scripted playtests and release material use low. Luna handles bounded reference research, approved content batches, scripted playtests and release material. Broader research, complex content or release engineering can be reassigned to Sol. Escalate difficult unresolved findings by narrowing the ticket or reassigning it to Sol at medium effort. Use only Sol and Luna with medium or low effort for studio routing, following the Director's restrictions. Do not escalate beyond medium. Preserve ownership and review independence when escalating.

## Loading and maintenance

Codex custom agents use `.codex/agents/*.toml`, with `name`, `description`, `developer_instructions`, `model` and `model_reasoning_effort`. Claude's `model: opus` and `model: sonnet` are retained exclusively in `.claude/agents/`; replacing those values would not configure Codex.

In the skill source, edit role instructions in `assets/plantilla/.claude/agents/` and model assignments in `scripts/generate_codex_agents.py`, then run that script and its `--check` mode. Update this table when changing routing. Regeneration affects the skill template only. The installer preserves existing project files: review `PRESERVED` entries and merge intended role changes manually, including local Codex customizations.

The main session model and global Codex configuration are not changed. Do not assume named-agent discovery or model overrides work in every host. Check the selected models in the actual client before relying on routing. If unavailable, report it and use an explicitly selected available alternative; do not silently claim the configured model ran. No live model calls are required to install these profiles.

Sources: [official custom-agent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents) and [official model guidance](https://learn.chatgpt.com/docs/models).
