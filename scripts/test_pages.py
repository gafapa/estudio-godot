#!/usr/bin/env python3
"""Check publication boundaries and archive reproducibility without external services."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location("pages_builder", Path(__file__).with_name("build_pages.py"))
BUILDER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BUILDER)


class PublicationTests(unittest.TestCase):
    def test_archive_is_reproducible_and_excludes_local_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("assets", "references", "scripts", "site", ".git", ".validation", "scripts/__pycache__"):
                (root / name).mkdir(parents=True, exist_ok=True)
            (root / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
            (root / "scripts/example.py").write_text("print('example')\n", encoding="utf-8")
            (root / "site/index.html").write_text("<!doctype html>", encoding="utf-8")
            for name in (".git/config", ".validation/private.log", "scripts/__pycache__/example.pyc", "site/private.txt"):
                (root / name).write_text("must not publish", encoding="utf-8")
            archive, count, first = BUILDER.build(root)
            with zipfile.ZipFile(archive) as bundle:
                self.assertEqual(set(bundle.namelist()), {"estudio-godot/SKILL.md", "estudio-godot/scripts/example.py"})
            self.assertEqual(count, 2)
            self.assertEqual(first, BUILDER.build(root)[2])

    def test_missing_source_cannot_publish_a_partial_download(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                BUILDER.build(Path(temporary))


if __name__ == "__main__":
    unittest.main(verbosity=2)
