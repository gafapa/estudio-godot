#!/usr/bin/env python3
"""Local regression tests. Real Godot/export/device qualification is separate."""
import ast
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "assets/plantilla"
BASH = shutil.which("bash")
if not BASH and os.name == "nt" and shutil.which("git"):
    BASH = str(Path(shutil.which("git")).parent.parent / "bin/bash.exe")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INSTALLER = load_module("studio_installer", ROOT / "scripts/instalar.py")
PARSER = load_module("test_log_parser", TEMPLATE / "tools/parse_test_log.py")
ZONE = load_module("zone_checker", TEMPLATE / "tools/check_zone.py")
ANDROID = load_module("android_smoke", TEMPLATE / "tools/android_smoke.py")
CODEX = load_module("codex_profiles", ROOT / "scripts/generate_codex_agents.py")
CACHE = load_module("validation_cache_tests", TEMPLATE / "tools/validation_cache.py")
METRICS = load_module("workflow_metrics_tests", TEMPLATE / "tools/workflow_metrics.py")
IDLE = load_module("idle_godot_tests", TEMPLATE / "tools/wait_for_godot.py")
OWNED = load_module("owned_process_tests", ROOT / "scripts/test_owned_godot.py")
OwnedProcessTests = OWNED.OwnedProcessTests


class QuietEngineTests(unittest.TestCase):
    def test_bounded_hidden_command_preserves_output_and_exit_code(self):
        result = subprocess.run([sys.executable, str(TEMPLATE / "tools/run_bounded.py"), "15",
                                 sys.executable, "-c", "import sys; print('hidden-output-ok'); sys.exit(7)"],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertIn("hidden-output-ok", result.stdout)

    def test_wait_yields_to_other_engines_and_never_terminates_them(self):
        states = iter([[{"ProcessId": 42, "Name": "Godot.exe"}], []])
        pauses = []
        self.assertTrue(IDLE.wait_for_idle(10, detect=lambda: next(states), now=lambda: 0, pause=pauses.append))
        self.assertEqual(pauses, [5])
        now = [0]
        def pause(seconds):
            now[0] += seconds
        self.assertFalse(IDLE.wait_for_idle(2, detect=lambda: [{"ProcessId": 42, "Name": "Godot.exe"}],
                                           now=lambda: now[0], pause=pause))
        self.assertEqual(now[0], 2)

    @unittest.skipUnless(os.name == "nt", "Windows process inventory")
    def test_invalid_process_inventory_fails_closed(self):
        for output in ('{}', '[{"ProcessId":true,"Name":"Godot.exe"}]', 'not json'):
            with self.subTest(output=output), patch.object(IDLE.shutil, "which", return_value="powershell.exe"), patch.object(IDLE.subprocess, "run", return_value=SimpleNamespace(stdout=output)):
                with self.assertRaises((ValueError, RuntimeError)):
                    IDLE.inventory()


class EvidenceTests(unittest.TestCase):
    def test_fingerprint_tracks_tools_packages_environment_and_ignores_shell_transport(self):
        with tempfile.TemporaryDirectory(prefix="studio-fingerprint-") as temporary:
            root = Path(temporary)
            (root / "tools").mkdir()
            tool = root / "tools/ci.sh"
            tool.write_text("first", encoding="utf-8")
            package = SimpleNamespace(metadata={"Name": "test-dependency"}, version="1", read_text=lambda _: "record-1")
            with patch.object(CACHE.shutil, "which", return_value=sys.executable), patch.object(CACHE.importlib.metadata, "distributions", return_value=[package]):
                first = CACHE.fingerprint(root, "sha", BASH, {"TOKEN": "private"})
                self.assertIsNotNone(first)
                self.assertNotIn("private", first)
                self.assertEqual(first, CACHE.fingerprint(root, "sha", BASH, {"TOKEN": "private", "SHLVL": "3", "PWD": "/other"}))
                self.assertNotEqual(first, CACHE.fingerprint(root, "sha", BASH, {"TOKEN": "changed"}))
                self.assertNotEqual(first, CACHE.fingerprint(root, "other-sha", BASH, {"TOKEN": "private"}))
                self.assertIsNone(CACHE.fingerprint(root, "sha", BASH, {"BASH_ENV": "/external"}))
                package.version = "2"
                self.assertNotEqual(first, CACHE.fingerprint(root, "sha", BASH, {"TOKEN": "private"}))
                package.version = "1"
                tool.write_text("second", encoding="utf-8")
                self.assertNotEqual(first, CACHE.fingerprint(root, "sha", BASH, {"TOKEN": "private"}))

    def test_receipts_reject_missing_corrupt_expired_or_failed_evidence(self):
        with tempfile.TemporaryDirectory(prefix="studio-evidence-") as temporary:
            base = Path(temporary)
            directory = base / "cache"
            log = base / "ci.log"
            log.write_text("CI_LOCAL_OK\n", encoding="utf-8")
            CACHE.save_receipt(directory, "key", "sha", log)
            self.assertIsNotNone(CACHE.load_receipt(directory, "key"))
            path = directory / "key.json"
            original = json.loads(path.read_text(encoding="utf-8"))
            for change in ({"completed_at": 0}, {"completed_at": CACHE.time.time() + 500},
                           {"returncode": 1}, {"key": "different"}, {"log": "../outside.log"}):
                path.write_text(json.dumps({**original, **change}), encoding="utf-8")
                self.assertIsNone(CACHE.load_receipt(directory, "key"))
            path.write_text(json.dumps(original), encoding="utf-8")
            log.write_text("Changed evidence", encoding="utf-8")
            self.assertIsNone(CACHE.load_receipt(directory, "key"))
            log.unlink()
            self.assertIsNone(CACHE.load_receipt(directory, "key"))
            path.write_text("not json", encoding="utf-8")
            self.assertIsNone(CACHE.load_receipt(directory, "key"))

    def test_local_metrics_report_measured_phases_and_reject_invalid_times(self):
        with tempfile.TemporaryDirectory(prefix="studio-metrics-") as temporary:
            root = Path(temporary)
            METRICS.record(root, "validation", 2, "T-1", cache_hit=True)
            METRICS.record(root, "review", 3, "T-1")
            METRICS.record(root, "escaped_defect", 0, "BUG-1", "failed")
            report = METRICS.summarize(root)
            self.assertEqual(report["seconds_by_phase"], {"validation": 2, "review": 3, "escaped_defect": 0})
            self.assertEqual(report["cache_hits"], 1)
            self.assertEqual(report["escaped_defects"], 1)
            for seconds in (-1, float("inf"), float("nan")):
                with self.assertRaises(ValueError):
                    METRICS.record(root, "review", seconds)


class CodexProfileTests(unittest.TestCase):
    def test_generated_profiles_cover_roles_and_are_current(self):
        profiles = CODEX.render_profiles()
        paths = {path.stem: path for path in (TEMPLATE / ".codex/agents").glob("*.toml")}
        self.assertEqual(paths.keys(), profiles.keys())
        for role, content in profiles.items():
            with self.subTest(role=role):
                self.assertEqual(paths[role].read_text(encoding="utf-8"), content)

    def test_codex_schema_models_and_role_instructions(self):
        try:
            import tomllib
        except ImportError:
            self.skipTest("TOML parsing requires Python 3.11+; generator supports Python 3.10")
        for role, content in CODEX.render_profiles().items():
            with self.subTest(role=role):
                profile = tomllib.loads(content)
                self.assertEqual(profile["name"], role)
                self.assertIsInstance(profile["description"], str)
                self.assertIn(profile["model"], ("gpt-6.1-sol", "gpt-6-luna"))
                self.assertIn(profile["model_reasoning_effort"], ("medium", "low"))
                self.assertIn("AGENTS.md", profile["developer_instructions"])
                self.assertIn("Allowed paths", profile["developer_instructions"])
                self.assertNotIn("tools", profile)
                self.assertNotIn("sandbox_mode", profile)

    def test_unassigned_role_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="studio-unassigned-role-") as temporary:
            template = Path(temporary)
            shutil.copytree(TEMPLATE / ".claude/agents", template / ".claude/agents")
            (template / ".claude/agents/new-role.md").write_text("Unassigned", encoding="utf-8")
            with self.assertRaises(ValueError):
                CODEX.render_profiles(template)


class ConfigurationTests(unittest.TestCase):
    def test_legacy_and_english_configuration_match(self):
        legacy = INSTALLER.configuration_values({"juego": "Test Game", "godot_version": "4.7.2", "modo": "automático"})
        english = INSTALLER.configuration_values({"game": "Test Game", "godot_version": "4.7.2", "mode": "automatic"})
        self.assertEqual(legacy, english)

    def test_invalid_configuration_is_rejected(self):
        for extra in ({"view_w": -1}, {"view_h": True}, {"dimension": "bad"}, {"mode": "bad"}, {"renderer": "bad"}, {"shot_res": "1x1;touch bad"}, {"executable": "../bad"}, {"package": "bad"}, {"game": "line\nbreak"}, {"unknown": 1}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                INSTALLER.configuration_values({"game": "Test", "godot_version": "4.7.2", **extra})

    def test_name_escaping_round_trips(self):
        name = 'The "Quoted" \\ Game'
        values = INSTALLER.configuration_values({"game": name, "godot_version": "4.7.2"})
        rendered = INSTALLER.render_template('config/name="{{GAME_NAME}}"', values, '.godot')
        self.assertEqual(json.loads(rendered.split('=', 1)[1]), name)


class MetadataTests(unittest.TestCase):
    def test_all_frontmatter_parses(self):
        import yaml
        for path in ROOT.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            if text.startswith("---\n"):
                with self.subTest(path=str(path.relative_to(ROOT))):
                    metadata = yaml.safe_load(text.split("---", 2)[1])
                    self.assertIsInstance(metadata["name"], str)
                    self.assertIsInstance(metadata["description"], str)

    def test_python_syntax(self):
        for path in ROOT.rglob("*.py"):
            with self.subTest(path=str(path.relative_to(ROOT))):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_bash_syntax_and_lf(self):
        self.assertTrue(BASH, "Git Bash is required for regression testing")
        for path in [*ROOT.rglob("*.sh"), TEMPLATE / "tools/hooks/pre-push"]:
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn(b"\r", path.read_bytes())
                result = subprocess.run([BASH, "-n", str(path)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)


class TestLogTests(unittest.TestCase):
    summary = "Overall Summary: 2 test cases | 0 errors | 0 failures | 0 skipped | 0 orphans\n"

    def test_healthy_suite_and_documented_warning_code(self):
        self.assertTrue(PARSER.evaluate(self.summary, 0)[0])
        self.assertTrue(PARSER.evaluate(self.summary, 101)[0])

    def test_empty_discovery_never_hides_failure(self):
        for code in (0, 2, 100, 101, 124):
            self.assertFalse(PARSER.evaluate("No test cases found", code)[0])

    def test_failed_empty_malformed_and_skipped_suites(self):
        for text, code in ((self.summary, 2), (self.summary.replace("2 test cases", "0 test cases"), 0), (self.summary.replace("0 skipped", "2 skipped"), 0), (self.summary.replace("0 orphans", "1 orphans"), 101), ("Overall Summary: nonsense", 0), (self.summary + "SCRIPT ERROR: bad", 0), ("ERROR: invalid debugger port\n" + self.summary, 0)):
            with self.subTest(text=text, code=code):
                self.assertFalse(PARSER.evaluate(text, code)[0])


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="studio-regression-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "project"
        self.config = self.base / "config.json"
        self.config.write_text(json.dumps({"game": "Test Game", "godot_version": "4.7.2"}), encoding="utf-8")
        self.install()
        self.git("config", "user.name", "Local Regression")
        self.git("config", "user.email", "local@example.invalid")

    def command(self, *arguments, input=None, environment=None, timeout=30):
        return subprocess.run(list(arguments), cwd=self.project, input=input, capture_output=True, text=True, timeout=timeout, env=environment)

    def git(self, *arguments):
        result = self.command("git", *arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def install(self, *arguments):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/instalar.py"), "--config", str(self.config), "--destination", str(self.project), *arguments], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def stub_ci(self):
        # Observe actual snapshot content, cleanliness and SHA.
        (self.project / "tools/ci.sh").write_text('''#!/usr/bin/env bash
set -eu
if [ "${2:-}" = --commit ]; then
  exec "${PYTHON:-python}" tools/validate_commit.py --commit "$3" --quick
fi
[ -z "$(git status --porcelain)" ] || exit 20
SHA="$(git rev-parse HEAD)"
if [ -n "${VALIDATION_LOG:-}" ]; then printf '%s\\n' "$SHA" >> "$VALIDATION_LOG"; fi
if [ -f behavior.txt ]; then cat behavior.txt; grep -q '^good$' behavior.txt; fi
sleep "${VALIDATION_DELAY:-0}"
''', encoding="utf-8", newline="\n")

    def cache_environment(self):
        environment = dict(os.environ, GODOT=sys.executable, VALIDATION_LOG=str(self.base / "runs.log"))
        for name in ("BASH_ENV", "ENV", "PYTHONPATH", "PYTHONHOME", "LD_PRELOAD", "LD_LIBRARY_PATH"):
            environment.pop(name, None)
        return environment

    def test_machine_evidence_reuse_fresh_and_damaged_log(self):
        self.stub_ci()
        sha = self.commit("cache baseline")
        environment = self.cache_environment()
        command = (sys.executable, "tools/validate_commit.py", "--commit", sha, "--quick")
        first = self.command(*command, environment=environment)
        second = self.command(*command, environment=environment)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertIn("cached=true", second.stdout)
        self.assertEqual((self.base / "runs.log").read_text().splitlines(), [sha])
        fresh = self.command(*command, "--fresh", environment=environment)
        self.assertEqual(fresh.returncode, 0, fresh.stdout + fresh.stderr)
        self.assertIn("cached=false", fresh.stdout)
        receipt = next((self.project / "tools/out/validation/cache").glob("*.json"))
        record = json.loads(receipt.read_text(encoding="utf-8"))
        log = self.project / "tools/out/validation" / record["log"]
        log.write_text("corrupt", encoding="utf-8")
        retried = self.command(*command, environment=environment)
        self.assertEqual(retried.returncode, 0, retried.stdout + retried.stderr)
        self.assertIn("cached=false", retried.stdout)
        self.assertEqual(len((self.base / "runs.log").read_text().splitlines()), 3)
        metrics = METRICS.summarize(self.project)
        self.assertEqual(metrics["cache_hits"], 1)
        self.assertEqual(metrics["events_by_phase"]["validation"], 4)

    def test_failed_fresh_execution_invalidates_older_success(self):
        self.stub_ci()
        ci = self.project / "tools/ci.sh"
        ci.write_text(ci.read_text(encoding="utf-8") + '\n[ ! -f "$VALIDATION_FAIL_FLAG" ]\n', encoding="utf-8", newline="\n")
        sha = self.commit("flaky external fixture")
        flag = self.base / "fail.flag"
        environment = {**self.cache_environment(), "VALIDATION_FAIL_FLAG": str(flag)}
        command = (sys.executable, "tools/validate_commit.py", "--commit", sha, "--quick")
        first = self.command(*command, environment=environment)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        flag.touch()
        failed = self.command(*command, "--fresh", environment=environment)
        retry = self.command(*command, environment=environment)
        self.assertNotEqual(failed.returncode, 0)
        self.assertNotEqual(retry.returncode, 0)
        self.assertNotIn("cached=true", retry.stdout)

    def test_ci_wrapper_forwards_fresh_and_full_ci_never_uses_quick_cache(self):
        for name in ("lint.sh", "validate_data.sh", "test.sh", "export.sh", "pc_smoke.sh"):
            (self.project / "tools" / name).write_text(
                f'#!/usr/bin/env bash\nprintf "%s\\n" "{name}" >> "$VALIDATION_LOG"\n', encoding="utf-8", newline="\n")
        sha = self.commit("simulated full CI")
        environment = self.cache_environment()
        command = (BASH, "tools/ci.sh", "--quick", "--commit", sha)
        for arguments, cached in ((command, False), (command, True), ((*command, "--fresh"), False)):
            result = self.command(*arguments, environment=environment)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(f"cached={str(cached).lower()}", result.stdout)
        for _ in range(2):
            result = self.command(BASH, "tools/ci.sh", "--commit", sha, environment=environment)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("cached=false", result.stdout)
        commands = (self.base / "runs.log").read_text().splitlines()
        self.assertEqual(commands.count("test.sh"), 4)
        self.assertEqual(commands.count("export.sh"), 4)

    def test_cache_invalidates_tools_environment_sha_and_never_reuses_failures(self):
        self.stub_ci()
        (self.project / "behavior.txt").write_text("good\n", encoding="utf-8")
        sha = self.commit("good cache baseline")
        environment = self.cache_environment()
        command = (sys.executable, "tools/validate_commit.py", "--commit", sha, "--quick")
        for extra in ({}, {"CACHE_TEST_CONTEXT": "changed"}):
            result = self.command(*command, environment={**environment, **extra})
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("cached=false", result.stdout)
        (self.project / "tools/context.txt").write_text("changed tool", encoding="utf-8")
        result = self.command(*command, environment=environment)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("cached=false", result.stdout)
        (self.project / "behavior.txt").write_text("bad\n", encoding="utf-8")
        failed_sha = self.commit("bad new commit")
        for _ in range(2):
            result = self.command(sys.executable, "tools/validate_commit.py", "--commit", failed_sha, "--quick", environment=environment)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("cached=true", result.stdout)
        self.assertEqual((self.base / "runs.log").read_text().splitlines(), [sha, sha, sha, failed_sha, failed_sha])

    def test_cached_ci_does_not_skip_changed_zone_policy(self):
        self.stub_ci()
        ticket = self.project / "docs/backlog/cache.md"
        ticket.write_text("### CACHE-01 - Behavior\n- **Allowed paths:** `behavior.txt`\n", encoding="utf-8")
        self.commit("zone baseline")
        (self.project / "behavior.txt").write_text("good\n", encoding="utf-8")
        sha = self.commit("zone behavior")
        base = self.git("rev-parse", "HEAD~1")
        environment = self.cache_environment()
        command = (sys.executable, "tools/validate_commit.py", "--commit", sha, "--quick", "--ticket", "CACHE-01", "--base", base)
        first = self.command(*command, environment=environment)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        ticket.write_text("### CACHE-01 - Behavior\n- **Allowed paths:** `other.txt`\n", encoding="utf-8")
        rejected = self.command(*command, environment=environment)
        self.assertNotEqual(rejected.returncode, 0, rejected.stdout + rejected.stderr)
        self.assertNotIn("cached=true", rejected.stdout)

    def test_focused_checks_preserve_test_target_and_fail_closed(self):
        for name in ("lint.sh", "validate_data.sh"):
            (self.project / "tools" / name).write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8", newline="\n")
        test = self.project / "tools/test.sh"
        test.write_text('#!/usr/bin/env bash\n[ "$1" = tests/unit/game ]\n', encoding="utf-8", newline="\n")
        result = self.command(BASH, "tools/dev_check.sh", "tests/unit/game")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("DEV_CHECK_ONLY", result.stdout)
        test.write_text("#!/usr/bin/env bash\nexit 9\n", encoding="utf-8", newline="\n")
        failed = self.command(BASH, "tools/dev_check.sh", "tests/unit/game")
        self.assertEqual(failed.returncode, 9)
        self.assertNotIn("DEV_CHECK_ONLY", failed.stdout)

    def test_engine_guard_defaults_headless_and_releases_lease_during_gap(self):
        engine = self.project / "fake-engine.sh"
        engine.write_text('#!/usr/bin/env bash\n[ "$1" = --headless ] || exit 81\necho GUARDED_HELPER_OK\n', encoding="utf-8", newline="\n")
        engine.chmod(engine.stat().st_mode | 0o111)
        lock = self.base / "shared-machine.lock"
        environment = dict(os.environ, GODOT_REAL=engine.as_posix(), GODOT_MACHINE_LOCK=lock.as_posix(), GODOT_YIELD_SECONDS="2", GODOT_IDLE_WAIT="0")
        started = __import__("time").monotonic()
        result = self.command(BASH, "tools/godot_guarded.sh", environment=environment, timeout=25)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("GUARDED_HELPER_OK", result.stdout)
        self.assertIn("GODOT_OWNED_CLEANUP_OK", result.stderr)
        self.assertIn("active=0", result.stderr)
        self.assertIn("GODOT_YIELD: 2s", result.stderr)
        self.assertGreaterEqual(__import__("time").monotonic() - started, 2)
        self.assertFalse(lock.exists())
        self.assertFalse(Path(str(lock) + ".reap").exists())
        environment["GODOT_YIELD_SECONDS"] = "0"
        rejected = self.command(BASH, "tools/godot_guarded.sh", environment=environment)
        self.assertEqual(rejected.returncode, 2)

    def test_reinstall_preserves_files_and_hooks(self):
        scene = self.project / "src/game/main.gd"
        scene.write_text("custom\n", encoding="utf-8")
        self.git("config", "core.hooksPath", "existing-hooks")
        self.install()
        self.assertEqual(scene.read_text(), "custom\n")
        self.assertEqual(self.git("config", "core.hooksPath"), "existing-hooks")

    def test_reinstall_preserves_default_git_hook(self):
        self.git("config", "--unset", "core.hooksPath")
        hook = self.project / ".git/hooks/pre-push"
        hook.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
        self.install()
        result = self.command("git", "config", "--get", "core.hooksPath")
        self.assertEqual(result.returncode, 1)
        self.assertIn("exit 7", hook.read_text())

    def test_dry_run_writes_nothing(self):
        target = self.base / "dry"
        result = subprocess.run([sys.executable, str(ROOT / "scripts/instalar.py"), "--config", str(self.config), "--destination", str(target), "--dry-run"], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(target.exists())

    def test_codex_install_and_reinstall_preserve_model_customizations(self):
        self.assertTrue((self.project / "AGENTS.md").is_file())
        for source in (TEMPLATE / ".codex/agents").glob("*.toml"):
            self.assertEqual((self.project / ".codex/agents" / source.name).read_bytes(), source.read_bytes())
        profile = self.project / ".codex/agents/arquitecto.toml"
        customized = profile.read_text(encoding="utf-8").replace('model_reasoning_effort = "medium"', 'model_reasoning_effort = "low"')
        profile.write_text(customized, encoding="utf-8", newline="\n")
        config = self.project / ".codex/config.toml"
        config.write_text('model = "gpt-6-luna"\n', encoding="utf-8")
        self.install()
        self.assertEqual(profile.read_text(encoding="utf-8"), customized)
        self.assertEqual(config.read_text(encoding="utf-8"), 'model = "gpt-6-luna"\n')

    def test_missing_values_fail_without_waiting(self):
        for command in (["tools/screenshot.sh", "res://src/game/main.tscn", "1920x1080", "--frames"], ["tools/screenshot.sh", "res://src/game/main.tscn", "1920x1080", "--fixture"], ["tools/android_smoke.sh", "--scene"]):
            with self.subTest(command=command):
                result = self.command(BASH, *command, timeout=5)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_unpersonalized_project_is_not_ready(self):
        result = self.command(sys.executable, "tools/verify_project.py", ".", "--quick")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("VERIFY_FAILED", result.stdout)
        self.assertNotIn("VERIFY_PARTIAL_OK", result.stdout)

    def personalize(self):
        for path in [self.project / "CLAUDE.md", *(self.project / "docs").rglob("*.md")]:
            path.write_text(path.read_text(encoding="utf-8").replace("TODO:", "Decision:"), encoding="utf-8", newline="\n")
        for relative in ["docs/design/gameplay.md", "docs/design/personajes.md", "docs/design/ux/pantallas.md", "docs/referencias/mecanicas.md"]:
            path = self.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Test design\nDefined for regression verification.\n", encoding="utf-8")

    def test_quick_readiness_never_certifies_engine(self):
        self.personalize()
        result = self.command(sys.executable, "tools/verify_project.py", ".", "--quick")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("VERIFY_PARTIAL_OK", result.stdout)
        self.assertNotIn("\nVERIFY_OK", result.stdout)

    def test_invalid_agent_metadata_blocks_personalized_project(self):
        self.personalize()
        (self.project / ".claude/agents/qa-tester.md").write_text("---\nname: qa-tester\ndescription: bad: metadata\n---\n", encoding="utf-8")
        result = self.command(sys.executable, "tools/verify_project.py", ".", "--quick")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid metadata", result.stdout)

    def test_test_script_rejects_failed_discovery_end_to_end(self):
        runner = self.project / "addons/gdUnit4/bin/GdUnitCmdTool.gd"
        runner.parent.mkdir(parents=True)
        runner.write_text("# Simulated runner\n", encoding="utf-8")
        engine = self.project / "fake-engine.sh"
        engine.write_text('''#!/usr/bin/env bash
for arg in "$@"; do [ "$arg" != --import ] || exit 0; done
echo 'No test cases found'
exit 2
''', encoding="utf-8", newline="\n")
        engine.chmod(engine.stat().st_mode | 0o111)
        environment = dict(os.environ, GODOT=str(engine), GODOT_ALLOW_EDITOR="1", TEST_TIMEOUT="10")
        result = self.command(BASH, "tools/test.sh", environment=environment, timeout=25)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("TESTS_FAILED", result.stdout + result.stderr)
        self.assertIn("exit code 2", result.stdout + result.stderr)

    def test_test_script_runs_nonempty_suite_end_to_end(self):
        runner = self.project / "addons/gdUnit4/bin/GdUnitCmdTool.gd"
        runner.parent.mkdir(parents=True)
        runner.write_text("# Simulated runner\n", encoding="utf-8")
        engine = self.project / "fake-engine.sh"
        engine.write_text('''#!/usr/bin/env bash
for arg in "$@"; do [ "$arg" != --import ] || exit 0; done
echo 'Overall Summary: 2 test cases | 0 errors | 0 failures | 0 skipped | 0 orphans'
exit 0
''', encoding="utf-8", newline="\n")
        engine.chmod(engine.stat().st_mode | 0o111)
        environment = dict(os.environ, GODOT=str(engine), GODOT_ALLOW_EDITOR="1", TEST_TIMEOUT="10")
        result = self.command(BASH, "tools/test.sh", environment=environment, timeout=25)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("TESTS_OK", result.stdout)

    def test_gate_ignores_dirty_worktree(self):
        self.stub_ci()
        (self.project / "docs/backlog/test.md").write_text("### TEST-01 - Behavior\n- **Allowed paths:** `behavior.txt`\n", encoding="utf-8")
        self.commit("baseline")
        self.git("checkout", "-qb", "feat/test")
        (self.project / "behavior.txt").write_text("good\n", encoding="utf-8")
        sha = self.commit("valid behavior")
        (self.project / "behavior.txt").write_text("bad\n", encoding="utf-8")
        result = self.command(BASH, "tools/gate.sh", "feat/test", "TEST-01", "main")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"GATE_OK commit={sha}", result.stdout)
        self.assertEqual((self.project / "behavior.txt").read_text(), "bad\n")

    def test_zone_rejects_rename_from_outside(self):
        (self.project / "outside.txt").write_text("important", encoding="utf-8")
        (self.project / "docs/backlog/test.md").write_text("### TEST-02 - Rename\n- **Allowed paths:** `owned/**`\n", encoding="utf-8")
        self.commit("baseline")
        self.git("checkout", "-qb", "feat/rename")
        (self.project / "owned").mkdir()
        self.git("mv", "outside.txt", "owned/inside.txt")
        self.commit("rename")
        result = self.command(BASH, "tools/check_zone.sh", "HEAD", "TEST-02", "main")
        self.assertEqual(result.returncode, 1)
        self.assertIn("outside.txt", result.stderr)

    def test_concurrent_gates_have_independent_worktrees(self):
        self.stub_ci()
        (self.project / "docs/backlog/test.md").write_text("### TEST-03 - Behavior\n- **Allowed paths:** `behavior.txt`\n", encoding="utf-8")
        self.commit("baseline")
        self.git("checkout", "-qb", "feat/concurrent")
        (self.project / "behavior.txt").write_text("good\n", encoding="utf-8")
        sha = self.commit("behavior")
        environment = dict(os.environ, VALIDATION_DELAY="1")
        command = [BASH, "tools/gate.sh", sha, "TEST-03", "main"]
        processes = [subprocess.Popen(command, cwd=self.project, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, stdout + stderr)
        self.assertEqual(self.git("worktree", "list", "--porcelain").count("worktree "), 1)

    def test_push_checks_outgoing_tip_instead_of_head(self):
        self.stub_ci()
        (self.project / "behavior.txt").write_text("good\n", encoding="utf-8")
        head = self.commit("good current branch")
        self.git("checkout", "-qb", "other")
        (self.project / "behavior.txt").write_text("bad\n", encoding="utf-8")
        outgoing = self.commit("bad outgoing branch")
        self.git("checkout", "main")
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        log = self.base / "validated.log"
        environment = dict(os.environ, VALIDATION_LOG=str(log))
        update = f"refs/heads/other {outgoing} refs/heads/other {'0'*40}\n"
        result = self.command(BASH, "tools/hooks/pre-push", input=update, environment=environment)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(log.read_text().strip(), outgoing)

    def test_push_handles_ref_deletions(self):
        self.stub_ci()
        sha = self.commit("baseline")
        log = self.base / "validated.log"
        environment = dict(os.environ, VALIDATION_LOG=str(log))
        update = f"refs/heads/main {sha} refs/heads/main {'0'*40}\n(delete) {'0'*40} refs/heads/deleted {sha}\n"
        result = self.command(BASH, "tools/hooks/pre-push", input=update, environment=environment)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(log.read_text().splitlines(), [sha])


class AndroidTests(unittest.TestCase):
    def test_existing_emulator_selection_never_stops_it(self):
        commands = []
        def fake(command, **kwargs):
            commands.append(command)
            return SimpleNamespace(stdout=b"List of devices attached\nemulator-5554\tdevice\n", returncode=0, stderr=b"")
        with patch.object(ANDROID, "run", side_effect=fake), patch.dict(os.environ, {}, clear=True):
            self.assertEqual(ANDROID.select_device("adb"), "emulator-5554")
        self.assertEqual(commands, [["adb", "devices"]])

    def test_restore_user_state_on_success_and_failure(self):
        for crash in (False, True):
            with self.subTest(crash=crash), tempfile.TemporaryDirectory(prefix="android-fake-") as temporary:
                root = Path(temporary)
                apk = root / "game.apk"
                apk.write_bytes(b"fake apk")
                commands, writes = [], {}
                backups = {"launch.json": b'{"existing":true}', "launch_shot.png": ANDROID.PNG_HEADER + b"image"}
                def fake(command, **kwargs):
                    commands.append(command)
                    tail = command[3:]
                    stdout = b""
                    if tail[:2] == ["install", "-r"]:
                        stdout = b"Success\n"
                    elif tail[:5] == ["shell", "settings", "get", "global", "stay_on_while_plugged_in"]:
                        stdout = b"7\n"
                    elif "pidof" in tail:
                        stdout = b"1234\n"
                    elif "date" in tail:
                        stdout = b"10-17_12:00:00.000\n"
                    elif tail and tail[0] == "logcat":
                        stdout = b"LAUNCH_OPTIONS scene=res://scene.tscn\n" + (b"SCRIPT ERROR: failure\n" if crash else b"")
                    elif tail[:1] == ["exec-out"] and "cat" in tail:
                        stdout = backups[tail[-1].split('/')[-1]]
                    if kwargs.get("data") is not None:
                        writes[tail[-1]] = kwargs["data"]
                    return SimpleNamespace(stdout=stdout, stderr=b"", returncode=0)
                args = SimpleNamespace(no_export=True, scene="res://scene.tscn", arg=['message=a "quote" and \\ slash'], perf=None, shot=1, wait=1)
                with patch.object(ANDROID, "ROOT", root), patch.object(ANDROID, "APK", apk), patch.object(ANDROID, "run", side_effect=fake), patch.object(ANDROID.time, "sleep"):
                    if crash:
                        with self.assertRaises(RuntimeError):
                            ANDROID.smoke(args, "adb", "device")
                    else:
                        ANDROID.smoke(args, "adb", "device")
                self.assertTrue(any(command[3:5] == ["install", "-r"] for command in commands))
                self.assertFalse(any("uninstall" in command or "kill-server" in command or "emu" in command for command in commands))
                self.assertTrue(any(command[-2:] == ["stay_on_while_plugged_in", "7"] for command in commands))
                self.assertEqual(writes["'cat > files/launch.json'"], backups["launch.json"])
                self.assertEqual(writes["'cat > files/launch_shot.png'"], backups["launch_shot.png"])
                options = [value for key, value in writes.items() if "mkdir -p" in key]
                self.assertEqual(json.loads(options[0])["args"]["message"], 'a "quote" and \\ slash')


if __name__ == "__main__":
    unittest.main(verbosity=2)
