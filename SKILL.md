---
name: estudio-godot
description: Set up or operate a Godot 4 game development studio with reference research, game design, specialized Codex or Claude Code agents, isolated worktrees, local quality gates, playtests and milestone reviews. Use for a new game or to add this workflow to an existing Godot project.
---

# Godot game studio

Turn a game idea into a playable project through research, design, implementation, independent review, QA and playtesting. The main session is the Producer; the user is the Director and controls product scope and creative direction.

## Language policy

**Write all project and skill documentation in English. Write code identifiers (variables, functions, classes and constants), comments, docstrings, technical reports and commit messages in English.** Apply this rule to generated files and every agent assignment. Game dialogue, interface text and translations follow the game's localization requirements; they do not change the documentation or code language.

## Operating boundaries

- Preserve the user's chosen game, constraints and existing decisions. Installing the studio does not authorize changing the product.
- Use automatic mode unless the user requests gated mode. Make reversible decisions within the authorized scope and record alternatives, evidence and how to reverse them in `docs/DIRECTOR.md`. In gated mode, wait for the Director at creative and milestone decisions.
- Existing authorization remains valid. Obtain authorization for spending, publication, or destruction of user work only when it has not already been given. Prepare the reviewable result before requesting approval.
- Parallelize only independent work with disjoint file ownership and available authorized agents. If delegation is unavailable, perform the same work sequentially; disclose that review was not independent.
- Use permissively licensed code, CC0 or original assets, and OFL fonts unless the user specifies otherwise. Record sources and licenses in `assets/LICENSES.md`.
- Use `tools/godot_guarded.sh` or tools that wrap it for bounded Godot runs. Prefer headless execution without windows or sound. Always close and verify the owned process tree after each test, release the machine lease and leave a five-second gap for other applications. Wait for other active engines without terminating them. Read [quiet Godot testing](assets/plantilla/docs/guides/quiet-godot-tests.md) for lifecycle controls and rendering exceptions. Never leave background engines or device sessions running.

## 1. Establish the project

For a new idea, establish the fantasy, core verb, provisional name, folder, 2D/3D, platforms, orientation, comparable games, budget and operating mode. Ask only for missing information that materially changes the result. Documentation and code language are fixed to English.

For an existing project, inspect `project.godot`, source, documentation and repository state. Preserve appropriate architecture; complete only missing design work. If `docs/AGENTES.md` and `.claude/skills/sprint/` exist, inspect their version and resume instead of reinstalling.

Detect the installed Godot version rather than guessing. For mobile, inspect `adb devices -l` only when device testing is in scope. Use the override resolution from `wm size` where present. An unavailable engine or device is a validation limitation, not evidence of success.

## 2. Research and vision

Read [references/investigacion.md](references/investigacion.md). Research comparable games by theme, central mechanic and player goal; split research among agents when useful. Write `docs/referencias/mecanicas.md`, then `docs/VISION.md`: one sentence, discriminating pillars, audience, platforms, exclusions, references and monetization constraints. Record unresolved decisions in the Director inbox.

## 3. Design a small prototype

Use the shared reference method and read only the relevant guides:

- [references/gameplay.md](references/gameplay.md): moment/session/meta loops, progression, measurable pacing, onboarding and the M1 cut. Write `docs/design/gameplay.md`.
- [references/personajes.md](references/personajes.md): entities, readable silhouettes, production methods, animation and sound. Write `docs/design/personajes.md` and `docs/arte/guia_estilo.md`.
- [references/interfaz.md](references/interfaz.md): screen map, navigation, HUD, platform controls, wireframes and accessibility. Write `docs/design/ux/pantallas.md`.

For spatial levels, visual production or audio implementation, read the relevant guide in [assets/plantilla/docs/guides/level-design.md](assets/plantilla/docs/guides/level-design.md), [technical-art.md](assets/plantilla/docs/guides/technical-art.md) or [audio.md](assets/plantilla/docs/guides/audio.md). These are installed as `docs/guides/` for project agents. Use blockout evidence, platform-specific budgets and audio lifecycle checks where applicable; skip unrelated deliverables. Keep existing roles and assign implementation paths explicitly.

Research can run in parallel after vision; write gameplay first, then character and interface designs using its loops. Keep documents short enough to support decisions. M1 should answer whether the central mechanic is worth developing. Preserve preproduction documents during installation.

## 4. Install and personalize

Run `python <skill>/scripts/instalar.py --help` for the configuration contract. Example:

```json
{"game":"Example Game","godot_version":"4.7.2","dimension":"2D","platforms":"PC","mode":"automatic"}
```

Use the detected version in real configurations. Run:

```bash
python <skill>/scripts/instalar.py --config config.json --destination <project> --dry-run
python <skill>/scripts/instalar.py --config config.json --destination <project> [--gdunit-from <local-project>]
```

The installer preserves existing files and hook configuration. Review `PRESERVED` entries and manually merge intended changes. If a different hook path is configured, chain `tools/hooks/pre-push` from it; do not disable existing hooks. Inspect remotes and authorization before any push.

Install compatible GdUnit4 and development requirements (`python -m pip install -r tools/requirements.txt`) when needed and authorized. Vendor GdUnit4 in the committed project so isolated validation uses the reviewed dependency; snapshots never copy mutable addons from a dirty checkout. The installer does not download addons. Choose isolated dependencies where possible.

Replace every `TODO`/legacy `ADAPTAR` marker in instructions and project documents. Set genre architecture using [references/arquitectura.md](references/arquitectura.md), adapt the 17 agent profiles, remove irrelevant roles and update ownership consistently. The Architect writes contracts; the Producer approves and integrates them. Set `ESTUDIO_WIP` within available agent capacity and `GODOT_SLOTS` within machine limits.

For Codex, use the installed `AGENTS.md` and `.codex/agents/*.toml`, with model/effort routing described in [the Codex model guide](assets/plantilla/docs/guides/codex-models.md). For Claude Code, retain `.claude/agents/` and its provider-specific model names. When editing template roles, regenerate Codex profiles with `python <skill>/scripts/generate_codex_agents.py`, then run its `--check` mode. Existing installed profiles require a reviewed merge because the installer preserves files. Verify the host's effective model selection; do not imply that Claude hooks or skills are automatically registered with Codex.

## 5. Verify before production

```bash
bash <skill>/scripts/verificar.sh <project> --quick
bash <skill>/scripts/verificar.sh <project>
```

Quick mode checks metadata, personalization, dependencies, lint and data but reports `VERIFY_PARTIAL_OK`; it never certifies engine execution. Full verification also checks the installed Godot version, GdUnit4, API dump and nonempty test execution. Only full success prints `VERIFY_OK`. Neither result proves export or device qualification; M0 covers those separately. Correct failures before relying on quality gates.

## 6. Start and continue production

Read [references/bucle.md](references/bucle.md). Set verifiable milestone criteria in `docs/PLAN.md` and publish tickets in `docs/backlog/`. The initial M0 tickets have disjoint ownership; respect their dependencies. Use project skills `investigar`, `spec`, `sprint`, `playtest` and `hito` as their stages become ready.

Use [the fast delivery guide](assets/plantilla/docs/guides/fast-delivery.md) to group coherent small tasks, keep specifications proportional, run focused development checks and reuse matching successful machine evidence. Low/medium-risk review responsibilities can share one qualified independent reviewer; critical work retains separate reviews. Run fresh complete test CI on the integrated SHA and track local workflow timings and escaped defects. Do not trade away acceptance criteria or independent judgment for speed.

Validate immutable commit SHAs, integrate sequentially and validate the resulting merge commit. Continue ready work within scope through M4, maintaining the Director inbox and reporting what to play. Prepare M5 artifacts locally; publication follows the user's existing authorization.

Persist ticket state, branch names, SHAs, evidence, decisions and next action. A session hook is a reminder, not a scheduler. Do not promise execution across closed sessions. Use scheduling only if the host actually supports it and the user requests it.

## Maintenance

Run `python <skill>/scripts/test_skill.py` after changes. It validates metadata and exercises installation, error handling, commit isolation, push gating, quiet-engine scheduling and Android behavior with local simulated tools, plus native Windows owned-process cleanup tests where supported. Report these separately from real Godot, export and hardware checks. When Godot and compatible GdUnit4 are available, execute the generated harness in an isolated fixture through the headless wrappers, retain logs, verify owned-process closure and leave the configured gaps between invocations.
