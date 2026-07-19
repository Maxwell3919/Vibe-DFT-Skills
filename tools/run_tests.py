#!/usr/bin/env python3
"""Discover and run all offline validation suites for active DFT Skills.

Controlled local hooks are ``tests/test_*.py`` (one unittest discovery run),
``scripts/test_*.py`` (direct script), ``scripts/check_*.py`` (direct check),
and ``scripts/sync_*.py`` (only when a literal argparse ``--check`` option is
declared, and always invoked in that mode). Non-active Skill trees are never
scanned. Any new active Skill without a local hook fails discovery.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import ast
from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Iterable

from registry_yaml import RegistryYAMLError, load_yaml_strict


CANONICAL_TEST_HOOK = re.compile(r"^test_[a-z0-9_]+\.py$")
CANONICAL_CHECK_HOOK = re.compile(r"^(?:check|sync)_[a-z0-9_]+\.py$")

# These two active Skills predate local test-hook directories. Their tests are
# intentionally retained in the repository-level tests/ suite. New active
# Skills must provide a local controlled hook; do not extend this set as a
# substitute for adding one.
ROOT_TEST_COVERED_SKILLS = frozenset({"dft-campaign-efficiency", "dft-postprocess"})
BYTECODE_ENV = "PYTHONDONTWRITEBYTECODE"
RUNNER_SCRIPT = Path(__file__).resolve()


class DiscoveryError(ValueError):
    """A stable, fail-closed test-discovery error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ActiveSkill:
    name: str
    relative_path: PurePosixPath
    absolute_path: Path


@dataclass(frozen=True)
class Command:
    label: str
    argv: tuple[str, ...]
    cwd: Path

    @property
    def identity(self) -> tuple[str, tuple[str, ...]]:
        return (str(self.cwd.resolve()), self.argv)


def _safe_relative_path(value: object) -> PurePosixPath | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path


def compile_python_tree(root: Path, relative_value: str) -> int:
    relative = _safe_relative_path(relative_value)
    if relative is None:
        print("COMPILE_ERROR SOURCE_PATH_INVALID", file=sys.stderr)
        return 2
    source_root = root.joinpath(*relative.parts)
    if source_root.is_symlink() or not source_root.is_dir():
        print("COMPILE_ERROR SOURCE_TREE_INVALID", file=sys.stderr)
        return 2
    for path in sorted(source_root.rglob("*.py"), key=lambda item: item.relative_to(source_root).as_posix()):
        if path.is_symlink() or not path.is_file():
            print("COMPILE_ERROR SOURCE_FILE_INVALID", file=sys.stderr)
            return 2
        try:
            text = path.read_text(encoding="utf-8")
            compile(text, path.relative_to(root).as_posix(), "exec")
        except (OSError, UnicodeError, SyntaxError):
            print("COMPILE_ERROR SOURCE_COMPILE_FAILED", file=sys.stderr)
            return 2
    return 0


def load_active_skills(root: Path) -> tuple[ActiveSkill, ...]:
    registry_path = root / "registry" / "skill-registry.yaml"
    try:
        registry = load_yaml_strict(registry_path)
    except (OSError, UnicodeError, RegistryYAMLError) as exc:
        raise DiscoveryError("REGISTRY_UNREADABLE", "the Skill registry cannot be read") from exc
    if not isinstance(registry, dict) or registry.get("schema_version") != "1.0":
        raise DiscoveryError("REGISTRY_SCHEMA_INVALID", "the Skill registry has an unsupported schema")
    skills = registry.get("skills")
    if not isinstance(skills, dict) or not skills:
        raise DiscoveryError("REGISTRY_SKILLS_INVALID", "the Skill registry has no skills mapping")
    if any(not isinstance(name, str) or not isinstance(specification, dict) for name, specification in skills.items()):
        raise DiscoveryError("REGISTRY_ENTRY_INVALID", "a Skill registry entry is malformed")

    active: list[ActiveSkill] = []
    resolved_paths: set[Path] = set()
    for name in sorted(skills):
        specification = skills[name]
        if specification.get("lifecycle") != "active":
            continue
        expected = PurePosixPath("skills", name)
        relative = _safe_relative_path(specification.get("path"))
        if relative != expected:
            raise DiscoveryError(
                "ACTIVE_SKILL_PATH_INVALID",
                "an active Skill does not use its canonical source path",
            )
        absolute = root.joinpath(*relative.parts)
        if absolute.is_symlink() or not absolute.is_dir() or not absolute.joinpath("SKILL.md").is_file():
            raise DiscoveryError(
                "ACTIVE_SKILL_SOURCE_MISSING",
                "an active Skill source is missing, aliased, or incomplete",
            )
        resolved = absolute.resolve()
        if resolved in resolved_paths:
            raise DiscoveryError(
                "ACTIVE_SKILL_PATH_DUPLICATE",
                "more than one active Skill resolves to the same source path",
            )
        resolved_paths.add(resolved)
        active.append(ActiveSkill(name=name, relative_path=relative, absolute_path=absolute))
    if not active:
        raise DiscoveryError("ACTIVE_SKILL_SET_EMPTY", "the registry contains no active Skills")
    return tuple(active)


def _canonical_hook_files(directory: Path, prefix: str, pattern: re.Pattern[str]) -> tuple[Path, ...]:
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        raise DiscoveryError("TEST_HOOK_DIRECTORY_INVALID", "a test-hook directory is aliased or not a directory")
    candidates = sorted(directory.glob(f"{prefix}*.py"), key=lambda item: item.name)
    hooks: list[Path] = []
    for path in candidates:
        if path.is_symlink() or not path.is_file():
            raise DiscoveryError("TEST_HOOK_FILE_INVALID", "a discovered test hook is aliased or not a file")
        if not pattern.fullmatch(path.name):
            raise DiscoveryError("TEST_HOOK_NAME_INVALID", "a discovered test hook has a noncanonical filename")
        hooks.append(path)
    return tuple(hooks)


def _declares_check_flag(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise DiscoveryError("CHECK_HOOK_UNREADABLE", "a check hook cannot be parsed") from exc
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument" or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and first.value == "--check":
            return True
    return False


def discover_skill_commands(
    root: Path,
    python: str,
    *,
    root_test_covered: frozenset[str] = ROOT_TEST_COVERED_SKILLS,
) -> tuple[Command, ...]:
    commands: list[Command] = []
    for skill in load_active_skills(root):
        relative = skill.relative_path.as_posix()
        hooks_found = 0

        tests_dir = skill.absolute_path / "tests"
        unittest_hooks = _canonical_hook_files(tests_dir, "test_", CANONICAL_TEST_HOOK)
        if unittest_hooks:
            hooks_found += len(unittest_hooks)
            commands.append(
                Command(
                    label=f"skill:{skill.name}:unittest:tests",
                    argv=(python, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"),
                    cwd=skill.absolute_path,
                )
            )

        scripts_dir = skill.absolute_path / "scripts"
        script_tests = _canonical_hook_files(scripts_dir, "test_", CANONICAL_TEST_HOOK)
        for hook in script_tests:
            hooks_found += 1
            commands.append(
                Command(
                    label=f"skill:{skill.name}:script-test:{hook.name}",
                    argv=(python, PurePosixPath("scripts", hook.name).as_posix()),
                    cwd=skill.absolute_path,
                )
            )

        direct_checks = _canonical_hook_files(scripts_dir, "check_", CANONICAL_CHECK_HOOK)
        for hook in direct_checks:
            hooks_found += 1
            commands.append(
                Command(
                    label=f"skill:{skill.name}:check:{hook.name}",
                    argv=(python, PurePosixPath("scripts", hook.name).as_posix()),
                    cwd=skill.absolute_path,
                )
            )

        sync_checks = _canonical_hook_files(scripts_dir, "sync_", CANONICAL_CHECK_HOOK)
        for hook in sync_checks:
            if not _declares_check_flag(hook):
                raise DiscoveryError(
                    "CHECK_HOOK_FLAG_MISSING",
                    "a sync hook does not declare the required offline --check mode",
                )
            hooks_found += 1
            commands.append(
                Command(
                    label=f"skill:{skill.name}:check:{hook.name}",
                    argv=(python, PurePosixPath("scripts", hook.name).as_posix(), "--check"),
                    cwd=skill.absolute_path,
                )
            )

        if hooks_found == 0 and skill.name not in root_test_covered:
            raise DiscoveryError(
                "ACTIVE_SKILL_TEST_HOOK_MISSING",
                "an active Skill has no controlled local test or check hook",
            )
        if hooks_found == 0:
            print(
                f"DISCOVER: {skill.name} is covered by repository-level tests; add a local hook in a future migration",
                flush=True,
            )

        # Compile all Python under the active Skill without assuming a fixed
        # software list. Compilation is kept separate from behavioral hooks.
        commands.append(
            Command(
                label=f"skill:{skill.name}:compile:{relative}",
                argv=(python, "-B", str(RUNNER_SCRIPT), "--compile-tree", relative),
                cwd=root,
            )
        )

    kind_order = {"unittest": 0, "script-test": 1, "check": 2, "compile": 3}

    def key(command: Command) -> tuple[str, int, str]:
        _, skill_name, kind, detail = command.label.split(":", 3)
        return (skill_name, kind_order[kind], detail)

    return ensure_unique_commands(sorted(commands, key=key))


def core_commands(root: Path, python: str) -> tuple[Command, ...]:
    return (
        Command("core:software-registry", (python, "tools/software_registry.py"), root),
        Command("core:skill-registry", (python, "tools/skill_registry.py"), root),
        Command("core:contract-enums", (python, "tools/sync_contract_codes.py"), root),
        Command("core:repository-audit", (python, "tools/audit_repository.py"), root),
        Command(
            "core:repository-tests",
            (python, "-m", "unittest", "discover", "-s", "tests", "-v"),
            root,
        ),
        Command(
            "core:compile-tools",
            (python, "-B", str(RUNNER_SCRIPT), "--compile-tree", "tools"),
            root,
        ),
    )


def ensure_unique_commands(commands: Iterable[Command]) -> tuple[Command, ...]:
    result: list[Command] = []
    identities: set[tuple[str, tuple[str, ...]]] = set()
    labels: set[str] = set()
    for command in commands:
        if command.identity in identities or command.label in labels:
            raise DiscoveryError("TEST_COMMAND_DUPLICATE", "test discovery produced a duplicate command")
        identities.add(command.identity)
        labels.add(command.label)
        result.append(command)
    return tuple(result)


def discover_commands(root: Path, python: str | None = None) -> tuple[Command, ...]:
    interpreter = python or sys.executable
    return ensure_unique_commands((*core_commands(root, interpreter), *discover_skill_commands(root, interpreter)))


def child_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment[BYTECODE_ENV] = "1"
    return environment


def execute_commands(commands: Iterable[Command]) -> int:
    environment = child_environment()
    if environment.get(BYTECODE_ENV) != "1":
        print("FAIL: runner normalized_exit=2 raw_exit=environment-policy", file=sys.stderr)
        return 2
    for command in commands:
        print(f"+ [{command.label}]", " ".join(command.argv), flush=True)
        try:
            result = subprocess.run(
                command.argv,
                cwd=command.cwd,
                env=environment,
                check=False,
            )
        except OSError:
            print(f"FAIL: {command.label} normalized_exit=2 raw_exit=not-started", file=sys.stderr)
            return 2
        if result.returncode != 0:
            print(
                f"FAIL: {command.label} normalized_exit=2 raw_exit={result.returncode}",
                file=sys.stderr,
            )
            return 2
    return 0


def main(root: Path | None = None, argv: tuple[str, ...] = ()) -> int:
    selected_root = root or Path(__file__).resolve().parents[1]
    if argv:
        if len(argv) == 2 and argv[0] == "--compile-tree":
            return compile_python_tree(root or Path.cwd(), argv[1])
        print("USAGE_ERROR: unsupported runner arguments", file=sys.stderr)
        return 2
    try:
        commands = discover_commands(selected_root)
    except DiscoveryError as exc:
        print(f"DISCOVERY_ERROR {exc.code}: {exc}", file=sys.stderr)
        return 2
    result = execute_commands(commands)
    if result != 0:
        return result
    print(f"PASS: {len(commands)} deterministic offline commands completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(argv=tuple(sys.argv[1:])))
