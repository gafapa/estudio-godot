#!/usr/bin/env python3
"""Build a deterministic skill download for the static GitHub Pages website."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE_FOLDERS = ("assets", "references", "scripts")


def source_files(root):
    paths = [root / "SKILL.md"]
    for name in SOURCE_FOLDERS:
        paths.extend((root / name).rglob("*"))
    for path in sorted(paths):
        if "__pycache__" in path.parts or path.suffix in (".pyc", ".pyo"):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlinks are not allowed in publication sources: {path}")
        if path.is_file():
            yield path


def build(root=ROOT):
    if (not (root / "SKILL.md").is_file() or not (root / "site/index.html").is_file()
            or not all((root / folder).is_dir() for folder in SOURCE_FOLDERS)):
        raise ValueError("The skill source and static website must exist")
    output = root / "site/downloads"
    output.mkdir(parents=True, exist_ok=True)
    archive = output / "estudio-godot.zip"
    files = list(source_files(root))
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(f"estudio-godot/{relative}", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if path.suffix == ".sh" or path.name == "pre-push" else 0o100644) << 16
            bundle.writestr(info, path.read_bytes())
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "estudio-godot.zip.sha256").write_text(f"{checksum}  estudio-godot.zip\n", encoding="utf-8")
    return archive, len(files), checksum


if __name__ == "__main__":
    archive, count, checksum = build()
    print(f"PAGES_BUILD_OK files={count} sha256={checksum} archive={archive}")
