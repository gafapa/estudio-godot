#!/usr/bin/env python3
"""Install the Godot studio without overwriting project files.

Required config: game, godot_version. Optional: slug, executable, dimension (2D/3D),
renderer, orientation (horizontal/vertical), view_w, view_h, platforms, package,
pitch, mode (automatic/gated), date, shot_res, device. Legacy Spanish config keys
and --destino are accepted. Documentation, code identifiers and comments are English.
"""
import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_ROOT / "assets/plantilla"
DIRECTORIES = "src/sim src/game/contracts src/ui/theme src/ui/components src/ui/screens src/world src/audio data/balance data/content data/playtest data/schemas i18n assets/audio shaders addons tests/unit tests/integration tests/golden tests/balance tests/visual tests/soak tests/fixtures prototypes tools/out docs/referencias docs/design/ux docs/backlog docs/reviews/arte docs/reviews/jugabilidad docs/playtests docs/contracts docs/adr docs/arte docs/hitos docs/retros docs/balance docs/lanzamiento".split()
ALIASES = {"juego": "game", "exe": "executable", "dim": "dimension", "orientacion": "orientation", "plataformas": "platforms", "paquete": "package", "modo": "mode", "fecha": "date", "dispositivo": "device"}
FEATURES = {"mobile": "Mobile", "forward_plus": "Forward Plus", "gl_compatibility": "GL Compatibility"}
MARKER = re.compile(r"\{\{([A-Z_]+)\}\}")


def configuration_values(config):
    if not isinstance(config, dict):
        raise ValueError("Configuration must be an object")
    config = dict(config)
    for old, new in ALIASES.items():
        if old in config:
            if new in config and config[new] != config[old]:
                raise ValueError(f"Conflicting keys: {old}, {new}")
            config[new] = config.pop(old)
    allowed = set("game godot_version slug executable dimension renderer orientation view_w view_h platforms package pitch mode date shot_res device".split())
    if set(config) - allowed:
        raise ValueError(f"Unknown keys: {sorted(set(config) - allowed)}")

    def text(key, default=None):
        value = config.get(key, default)
        if not isinstance(value, str) or (not value and key != "pitch"):
            raise ValueError(f"{key} must be a nonempty string")
        if any(ord(char) < 32 or ord(char) == 127 for char in value) or "{{" in value:
            raise ValueError(f"Unsupported control characters or template markers in {key}")
        return value

    def choice(key, default, options):
        value = text(key, default)
        if value not in options:
            raise ValueError(f"{key} must be one of {list(options)}")
        return value

    game = text("game")
    ascii_name = unicodedata.normalize("NFKD", game).encode("ascii", "ignore").decode()
    slug = text("slug", re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-"))
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", slug):
        raise ValueError("slug must start with a letter and contain lowercase letters, digits and hyphens")
    executable = text("executable", re.sub(r"[^A-Za-z0-9]", "", ascii_name.title()) or "Game")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", executable):
        raise ValueError("executable must be a filename stem starting with a letter")
    version = text("godot_version")
    if not re.fullmatch(r"4\.\d+(?:\.\d+)?", version):
        raise ValueError("godot_version must be a stable Godot 4 version, such as 4.7.2")
    renderer = choice("renderer", "mobile", FEATURES)
    orientation = choice("orientation", "horizontal", ("horizontal", "vertical"))
    dimension = choice("dimension", "2D", ("2D", "3D"))
    mode = text("mode", "automatic")
    mode = {"automático": "automatic", "con puertas": "gated"}.get(mode, mode)
    if mode not in ("automatic", "gated"):
        raise ValueError("mode must be automatic or gated")
    vertical = orientation == "vertical"
    width = config.get("view_w", 1080 if vertical else 1920)
    height = config.get("view_h", 2400 if vertical else 1080)
    if any(type(value) is not int or not 1 <= value <= 16384 for value in (width, height)):
        raise ValueError("view_w and view_h must be integers from 1 to 16384")
    package = text("package", f"com.{slug.replace('-', '')}.game")
    if not re.fullmatch(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){2,}", package):
        raise ValueError("package must be a lowercase Android application ID with at least three components")
    date = text("date", datetime.date.today().isoformat())
    datetime.date.fromisoformat(date)
    shots = text("shot_res", "1080x2400 1536x2048 1920x1080" if vertical else "1920x1080 2560x1440 1280x800")
    for resolution in shots.split():
        if not re.fullmatch(r"[1-9]\d*x[1-9]\d*", resolution) or any(int(part) > 16384 for part in resolution.split("x")):
            raise ValueError("shot_res must contain positive WIDTHxHEIGHT resolutions up to 16384")
    scale = 2 if vertical and max(width, height) > 1600 else 1
    return {
        "GAME_NAME": game, "SLUG": slug, "EXE": executable, "GODOT_VERSION": version,
        "GODOT_MINOR": ".".join(version.split(".")[:2]), "DIM": dimension, "RENDERER": renderer,
        "FEATURE": FEATURES[renderer], "VIEW_W": str(width), "VIEW_H": str(height),
        "WIN_W": str(max(1, width // scale)), "WIN_H": str(max(1, height // scale)),
        "ORIENTATION": "1" if vertical else "0", "PLATFORMS": text("platforms", "PC"),
        "PACKAGE": package, "PITCH": text("pitch", ""), "MODE": mode, "DATE": date,
        "SHOT_RES": " ".join(shots.split()), "DEVICE": text("device", "No device configured"),
    }


def render_template(source, values, suffix):
    def replace(match):
        value = values[match.group(1)]
        if suffix in (".godot", ".gd", ".tscn", ".tres"):
            return json.dumps(value, ensure_ascii=False)[1:-1]
        return value
    return MARKER.sub(replace, source)


def run_git(destination, *arguments):
    result = subprocess.run(["git", *arguments], cwd=destination, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Git command failed")
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True)
    parser.add_argument("--destination", "--destino", dest="destination", required=True)
    parser.add_argument("--gdunit-from", help="Project containing addons/gdUnit4")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        values = configuration_values(json.loads(Path(args.config).read_text(encoding="utf-8-sig")))
        destination = Path(args.destination).resolve()
        if destination == SKILL_ROOT or SKILL_ROOT in destination.parents:
            raise ValueError("Destination must be outside the skill source")
        if destination.exists() and not destination.is_dir():
            raise ValueError("Destination must be a directory")
        if shutil.which("git") is None:
            raise ValueError("Git is required; no files installed")
        addon_source = Path(args.gdunit_from).resolve() / "addons/gdUnit4" if args.gdunit_from else None
        if addon_source and not (addon_source / "plugin.cfg").is_file():
            raise ValueError(f"GdUnit4 plugin not found: {addon_source}")
        # Preflight all paths and render every file before making changes.
        for directory in DIRECTORIES:
            if not (destination / directory).resolve().is_relative_to(destination):
                raise ValueError(f"Directory symlink escapes destination: {directory}")
        rendered = []
        for source in sorted(TEMPLATE.rglob("*")):
            if not source.is_file() or "__pycache__" in source.parts:
                continue
            relative = source.relative_to(TEMPLATE)
            if not (destination / relative).resolve().is_relative_to(destination):
                raise ValueError(f"Symlink escapes destination: {relative}")
            raw = source.read_bytes()
            try:
                raw = render_template(raw.decode("utf-8"), values, source.suffix).encode("utf-8")
            except UnicodeDecodeError:
                pass
            rendered.append((relative, raw))
        for relative, raw in rendered:
            target = destination / relative
            if target.exists():
                print(f"PRESERVED {relative.as_posix()}")
                continue
            print(f"{'WOULD_CREATE' if args.dry_run else 'CREATED'} {relative.as_posix()}")
            if not args.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(raw)
                if target.suffix == ".sh" or relative.as_posix() == "tools/hooks/pre-push":
                    target.chmod(target.stat().st_mode | 0o111)
        if args.dry_run:
            return 0
        for directory in DIRECTORIES:
            (destination / directory).mkdir(parents=True, exist_ok=True)
        (destination / "tools/out/.gdignore").touch()
        addon_destination = destination / "addons/gdUnit4"
        if addon_source and not addon_destination.exists():
            shutil.copytree(addon_source, addon_destination)
        if not (addon_destination / "plugin.cfg").is_file():
            print("WARNING: Install a compatible GdUnit4 release before full verification")
        if not (destination / ".git").exists():
            run_git(destination, "init", "-b", "main")
        result = subprocess.run(["git", "config", "--get", "core.hooksPath"], cwd=destination, capture_output=True, text=True)
        existing_hooks = result.stdout.strip()
        traditional_hooks = Path(run_git(destination, "rev-parse", "--git-path", "hooks"))
        if not traditional_hooks.is_absolute():
            traditional_hooks = destination / traditional_hooks
        if not existing_hooks and (traditional_hooks / "pre-push").is_file():
            print("WARNING: Preserved the existing default pre-push hook; chain tools/hooks/pre-push before verification")
        elif not existing_hooks:
            run_git(destination, "config", "--local", "core.hooksPath", "tools/hooks")
        elif existing_hooks != "tools/hooks":
            print(f"WARNING: Preserved core.hooksPath={existing_hooks}; chain tools/hooks/pre-push from your existing hook before verification")
        print("INSTALL_OK: personalize TODO markers, then run scripts/verificar.sh")
        return 0
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f"INSTALL_FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
