# estudio-godot

A local Godot 4 development studio skill for Codex and Claude Code. Turn an idea into a small playable loop, then develop it through scoped tickets, independent review, immutable commit validation and milestone playtests.

**[Documentation website](https://gafapa.github.io/estudio-godot/)** · **[Skill instructions](SKILL.md)** · **[Roles and quality gates](assets/plantilla/docs/AGENTES.md)**

## Install for Codex

Clone this repository into your personal skills folder:

```bash
git clone https://github.com/gafapa/estudio-godot.git "$HOME/.codex/skills/estudio-godot"
```

Then invoke `$estudio-godot` in a Codex session. If the folder already exists, compare and merge it or update its existing Git checkout; preserve local customizations. The skill does not install Godot or make every host support custom agents.

## Set up a game project

Requirements: Python 3.10+, Git, Bash (Git Bash on Windows), an installed stable Godot 4 engine, and compatible GdUnit4 for engine tests. Development dependencies are pinned in `assets/plantilla/tools/requirements.txt`.

Create a `config.json` using the actual installed engine version. For example:

```json
{"game":"My Game","godot_version":"4.7.2","dimension":"2D","platforms":"PC","mode":"automatic"}
```

```bash
python scripts/instalar.py --config config.json --destination ../my-game --dry-run
python scripts/instalar.py --config config.json --destination ../my-game
```

The installer preserves existing files and hooks. Personalize the generated project, install compatible GdUnit4, and follow [SKILL.md](SKILL.md). Project documentation, code identifiers and comments are English; game-facing localization follows the game's needs.

## What is included

- Seventeen role profiles, with native Codex TOML and Claude Code definitions.
- Codex uses only `gpt-6.1-sol` and `gpt-6-luna`, with `medium` or `low` reasoning. See [model routing](assets/plantilla/docs/guides/codex-models.md).
- Prototype and milestone planning, reference research, scoped ownership and sequential integration.
- Immutable lint, data and nonempty test gates; independent behavior review and critical-system checks.
- [Faster delivery](assets/plantilla/docs/guides/fast-delivery.md) through focused development checks and conservative reuse of matching machine evidence.
- [Quiet engine testing](assets/plantilla/docs/guides/quiet-godot-tests.md): headless by default, verified owned-process closure, bounded runs and five-second lease-free gaps. Other applications' engines are left untouched.
- Conditional guides for level design, technical art and interactive audio.

The main session is the Producer; the user is the Director. Actual delegation, model availability, engine execution and device access depend on the host. The studio does not run after a session closes or publish games without authorization.

## Validation

On 2026-10-24, 49 local regression checks passed, including native Windows process-containment checks and simulated tool scenarios. A separate isolated fixture passed two real harness tests using Godot 4.7.2 and GdUnit4 6.2.2 in headless mode. Logs confirmed owned-process closure and five-second gaps; the final process inventory was empty. These results do not qualify rendering, audible quality, exports, hardware devices or other games.

```bash
python -m pip install -r assets/plantilla/tools/requirements.txt
python scripts/generate_codex_agents.py --check
python scripts/test_skill.py
python scripts/test_pages.py
python scripts/build_pages.py
```

GitHub Actions runs regression checks on Windows before deploying the static `site/` directory to GitHub Pages. It does not claim a real Godot run on the hosted runner. The Pages build creates a clean, deterministic skill ZIP and SHA-256 checksum from the skill's source folders; it excludes Git metadata, caches and local validation artifacts.

The website is self-contained, with local OFL-licensed Barlow fonts and no analytics. The specialized production guides link to the Agency Agents references that informed their workflows.
