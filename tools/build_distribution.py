#!/usr/bin/env python3
"""Build and verify a physical distribution containing only active Skill source."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Sequence

from registry_yaml import RegistryYAMLError, load_yaml_strict
from skill_registry import source_tree_digest


DISTRIBUTION_SCHEMA_VERSION = "1.0"
MANIFEST_NAME = "manifest.json"


class DistributionError(ValueError):
    """Fail-closed distribution build error."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _source_commit(root: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    value = completed.stdout.strip()
    return value if len(value) == 40 else "unknown"


def _load_active(root: Path) -> tuple[tuple[str, Path, str], ...]:
    try:
        registry = load_yaml_strict(root / "registry" / "skill-registry.yaml")
    except (OSError, UnicodeError, RegistryYAMLError) as exc:
        raise DistributionError("cannot read the Skill registry") from exc
    if not isinstance(registry, dict) or registry.get("schema_version") != "1.0":
        raise DistributionError("unsupported Skill registry schema")
    skills = registry.get("skills")
    if not isinstance(skills, dict) or not skills:
        raise DistributionError("Skill registry has no entries")

    active: list[tuple[str, Path, str]] = []
    for name in sorted(skills):
        specification = skills[name]
        if not isinstance(name, str) or not isinstance(specification, dict):
            raise DistributionError("malformed Skill registry entry")
        if specification.get("lifecycle") != "active":
            continue
        expected = PurePosixPath("skills", name)
        if specification.get("path") != expected.as_posix():
            raise DistributionError(f"{name}: active Skill path is not canonical")
        expected_hash = specification.get("source_tree_sha256")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            raise DistributionError(f"{name}: active Skill source hash is invalid")
        source = root.joinpath(*expected.parts)
        actual = source_tree_digest(source)
        if actual.sha256 != expected_hash:
            raise DistributionError(f"{name}: active Skill source hash does not match the registry")
        active.append((name, source, expected_hash))
    if not active:
        raise DistributionError("no active Skills are registered")
    return tuple(active)


def _copy_regular(source: Path, target: Path) -> tuple[int, str]:
    info = source.lstat()
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or info.st_nlink != 1:
        raise DistributionError(f"unsafe source file: {source}")
    raw = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    executable = bool(info.st_mode & stat.S_IXUSR)
    target.chmod(0o755 if executable else 0o644)
    return len(raw), hashlib.sha256(raw).hexdigest()


def build_distribution(root: Path, output: Path, *, force: bool = False) -> dict[str, Any]:
    selected_root = root.resolve()
    selected_output = output.resolve()
    if selected_output == selected_root or selected_output == selected_root / ".git":
        raise DistributionError("distribution output cannot replace the repository or .git")
    if selected_output.exists():
        if not force:
            raise DistributionError(f"output already exists: {selected_output}")
        if selected_output.is_symlink() or not selected_output.is_dir():
            raise DistributionError("existing output is not a safe directory")
        shutil.rmtree(selected_output)
    selected_output.mkdir(parents=True)

    active = _load_active(selected_root)
    file_entries: list[dict[str, Any]] = []
    skill_entries: list[dict[str, Any]] = []
    for name, source, expected_hash in active:
        digest = source_tree_digest(source)
        for item in digest.files:
            relative = PurePosixPath("skills", name, item.path)
            source_file = source.joinpath(*PurePosixPath(item.path).parts)
            target_file = selected_output.joinpath(*relative.parts)
            size, sha256 = _copy_regular(source_file, target_file)
            if size != item.size or sha256 != item.sha256:
                raise DistributionError(f"{name}/{item.path}: copy integrity mismatch")
            file_entries.append(
                {
                    "path": relative.as_posix(),
                    "bytes": size,
                    "sha256": sha256,
                }
            )
        skill_entries.append(
            {
                "skill_id": name,
                "source_path": f"skills/{name}",
                "source_tree_sha256": expected_hash,
                "file_count": len(digest.files),
            }
        )

    readme = (
        "# Vibe-DFT-Skills active-only distribution\n\n"
        "This directory is generated from the lifecycle registry. It contains only "
        "active Skill source. Development and planned Skill source and metadata are "
        "excluded. Active means repository-installable and routable; it does not "
        "establish local software availability, native execution, numerical "
        "convergence, physical validity, or scientific acceptance.\n"
    ).encode("utf-8")
    readme_path = selected_output / "README.md"
    readme_path.write_bytes(readme)
    readme_path.chmod(0o644)
    file_entries.append(
        {
            "path": "README.md",
            "bytes": len(readme),
            "sha256": hashlib.sha256(readme).hexdigest(),
        }
    )

    manifest = {
        "schema_version": DISTRIBUTION_SCHEMA_VERSION,
        "distribution_id": "vibe-dft-skills-active-only",
        "source_commit": _source_commit(selected_root),
        "active_skill_count": len(skill_entries),
        "skills": skill_entries,
        "files": sorted(file_entries, key=lambda item: item["path"]),
        "excluded_lifecycles": ["development", "planned"],
        "claim_boundary": {
            "native_execution": False,
            "numerical_convergence": False,
            "physical_validity": False,
            "scientific_acceptance": False,
        },
    }
    raw_manifest = (
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    (selected_output / MANIFEST_NAME).write_bytes(raw_manifest)
    (selected_output / MANIFEST_NAME).chmod(0o644)
    return manifest


def validate_distribution(root: Path, output: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = output / MANIFEST_NAME
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"manifest unreadable: {exc}"]
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "1.0":
        errors.append("manifest schema_version is invalid")
        return errors

    expected_active = {name for name, _path, _digest in _load_active(root)}
    declared = manifest.get("skills")
    if not isinstance(declared, list):
        errors.append("manifest skills must be a list")
        declared = []
    declared_names = {
        item.get("skill_id")
        for item in declared
        if isinstance(item, dict) and isinstance(item.get("skill_id"), str)
    }
    if declared_names != expected_active:
        errors.append(
            f"active Skill set mismatch: declared={sorted(declared_names)} "
            f"expected={sorted(expected_active)}"
        )

    skills_root = output / "skills"
    actual_names = (
        {path.name for path in skills_root.iterdir() if path.is_dir() and not path.is_symlink()}
        if skills_root.is_dir()
        else set()
    )
    if actual_names != expected_active:
        errors.append(
            f"distribution Skill directories mismatch: actual={sorted(actual_names)} "
            f"expected={sorted(expected_active)}"
        )

    file_entries = manifest.get("files")
    if not isinstance(file_entries, list):
        errors.append("manifest files must be a list")
        file_entries = []
    declared_paths: set[str] = set()
    for index, entry in enumerate(file_entries):
        if not isinstance(entry, dict):
            errors.append(f"files/{index}: entry is not an object")
            continue
        path_text = entry.get("path")
        if not isinstance(path_text, str):
            errors.append(f"files/{index}: path is invalid")
            continue
        path = PurePosixPath(path_text)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            errors.append(f"files/{index}: unsafe path")
            continue
        if path_text in declared_paths:
            errors.append(f"files/{index}: duplicate path")
            continue
        declared_paths.add(path_text)
        target = output.joinpath(*path.parts)
        try:
            info = target.lstat()
            raw = target.read_bytes()
        except OSError:
            errors.append(f"{path_text}: file is missing or unreadable")
            continue
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            errors.append(f"{path_text}: file is aliased or special")
            continue
        if entry.get("bytes") != len(raw):
            errors.append(f"{path_text}: byte count mismatch")
        if entry.get("sha256") != hashlib.sha256(raw).hexdigest():
            errors.append(f"{path_text}: sha256 mismatch")

    actual_files = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file() and path != manifest_path
    }
    if actual_files != declared_paths:
        errors.append(
            f"file inventory mismatch: actual-only={sorted(actual_files - declared_paths)} "
            f"declared-only={sorted(declared_paths - actual_files)}"
        )
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="build in a temporary directory and validate without writing dist/",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.check:
            with tempfile.TemporaryDirectory(prefix="vibe-dft-dist-") as temporary:
                output = Path(temporary) / "vibe-dft-skills"
                build_distribution(root, output)
                errors = validate_distribution(root, output)
        else:
            output = (args.output or root / "dist" / "vibe-dft-skills").resolve()
            build_distribution(root, output, force=args.force)
            errors = validate_distribution(root, output)
    except (DistributionError, OSError, ValueError) as exc:
        print(f"DISTRIBUTION_ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"DISTRIBUTION_INVALID: {error}", file=sys.stderr)
        return 2
    print(f"PASS: active-only distribution contains {len(_load_active(root))} Skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
