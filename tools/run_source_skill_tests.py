#!/usr/bin/env python3
"""Run controlled offline behavior tests for source-backed non-routable Skills."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from typing import Iterable, Sequence

from registry_yaml import RegistryYAMLError, load_yaml_strict


CANONICAL_TEST_HOOK = re.compile(r"^test_[a-z0-9_]+\.py$")
CANONICAL_CHECK_HOOK = re.compile(r"^(?:check|sync)_[a-z0-9_]+\.py$")
ALLOWED_LIFECYCLES = frozenset({"active", "development"})
BYTECODE_ENV = "PYTHONDONTWRITEBYTECODE"
OFFLINE_ENV = "VIBE_DFT_OFFLINE"
DEFAULT_TIMEOUT_SECONDS = 300


class DiscoveryError(ValueError):
    """Stable fail-closed discovery error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SourceSkill:
    name: str
    lifecycle: str
    relative_path: PurePosixPath
    absolute_path: Path


@dataclass(frozen=True)
class Command:
    label: str
    argv: tuple[str, ...]
    cwd: Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _safe_relative_path(value: object) -> PurePosixPath | None:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path


def _parse_lifecycles(value: str) -> frozenset[str]:
    selected = frozenset(part.strip() for part in value.split(",") if part.strip())
    if not selected or not selected.issubset(ALLOWED_LIFECYCLES):
        raise DiscoveryError(
            "LIFECYCLE_SELECTION_INVALID",
            "lifecycles must be a nonempty comma-separated subset of active,development",
        )
    return selected


def load_source_skills(
    root: Path,
    lifecycles: frozenset[str],
) -> tuple[SourceSkill, ...]:
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

    selected: list[SourceSkill] = []
    resolved_paths: set[Path] = set()
    for name in sorted(skills):
        specification = skills[name]
        if not isinstance(name, str) or not isinstance(specification, dict):
            raise DiscoveryError("REGISTRY_ENTRY_INVALID", "a Skill registry entry is malformed")
        lifecycle = specification.get("lifecycle")
        if lifecycle not in lifecycles:
            continue
        expected = PurePosixPath("skills", name)
        relative = _safe_relative_path(specification.get("path"))
        if relative != expected:
            raise DiscoveryError(
                "SOURCE_SKILL_PATH_INVALID",
                f"{name}: source-backed Skill does not use its canonical path",
            )
        absolute = root.joinpath(*relative.parts)
        if (
            absolute.is_symlink()
            or not absolute.is_dir()
            or not absolute.joinpath("SKILL.md").is_file()
        ):
            raise DiscoveryError(
                "SOURCE_SKILL_MISSING",
                f"{name}: source tree is missing, aliased, or incomplete",
            )
        resolved = absolute.resolve()
        if resolved in resolved_paths:
            raise DiscoveryError(
                "SOURCE_SKILL_PATH_DUPLICATE",
                "more than one source-backed Skill resolves to the same path",
            )
        resolved_paths.add(resolved)
        selected.append(
            SourceSkill(
                name=name,
                lifecycle=str(lifecycle),
                relative_path=relative,
                absolute_path=absolute,
            )
        )
    if not selected:
        raise DiscoveryError("SOURCE_SKILL_SET_EMPTY", "no Skills match the lifecycle selection")
    return tuple(selected)


def _canonical_hook_files(
    directory: Path,
    prefix: str,
    pattern: re.Pattern[str],
) -> tuple[Path, ...]:
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        raise DiscoveryError("TEST_HOOK_DIRECTORY_INVALID", f"{directory}: invalid hook directory")
    hooks: list[Path] = []
    for path in sorted(directory.glob(f"{prefix}*.py"), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file():
            raise DiscoveryError("TEST_HOOK_FILE_INVALID", f"{path}: invalid hook file")
        if pattern.fullmatch(path.name) is None:
            raise DiscoveryError("TEST_HOOK_NAME_INVALID", f"{path.name}: noncanonical hook name")
        hooks.append(path)
    return tuple(hooks)


def _declares_check_flag(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise DiscoveryError("CHECK_HOOK_UNREADABLE", f"{path}: cannot parse check hook") from exc
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "--check"
        ):
            return True
    return False


def discover_commands(
    root: Path,
    lifecycles: frozenset[str],
    python: str | None = None,
) -> tuple[Command, ...]:
    interpreter = python or sys.executable
    commands: list[Command] = []
    labels: set[str] = set()
    identities: set[tuple[str, tuple[str, ...]]] = set()

    for skill in load_source_skills(root, lifecycles):
        found = 0
        tests = _canonical_hook_files(
            skill.absolute_path / "tests",
            "test_",
            CANONICAL_TEST_HOOK,
        )
        if tests:
            found += len(tests)
            commands.append(
                Command(
                    label=f"{skill.lifecycle}:{skill.name}:unittest",
                    argv=(
                        interpreter,
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_*.py",
                        "-v",
                    ),
                    cwd=skill.absolute_path,
                )
            )

        scripts_dir = skill.absolute_path / "scripts"
        for hook in _canonical_hook_files(scripts_dir, "test_", CANONICAL_TEST_HOOK):
            found += 1
            commands.append(
                Command(
                    label=f"{skill.lifecycle}:{skill.name}:script-test:{hook.name}",
                    argv=(interpreter, PurePosixPath("scripts", hook.name).as_posix()),
                    cwd=skill.absolute_path,
                )
            )
        for hook in _canonical_hook_files(scripts_dir, "check_", CANONICAL_CHECK_HOOK):
            found += 1
            commands.append(
                Command(
                    label=f"{skill.lifecycle}:{skill.name}:check:{hook.name}",
                    argv=(interpreter, PurePosixPath("scripts", hook.name).as_posix()),
                    cwd=skill.absolute_path,
                )
            )
        for hook in _canonical_hook_files(scripts_dir, "sync_", CANONICAL_CHECK_HOOK):
            if not _declares_check_flag(hook):
                raise DiscoveryError(
                    "CHECK_HOOK_FLAG_MISSING",
                    f"{skill.name}/{hook.name}: sync hook lacks literal --check support",
                )
            found += 1
            commands.append(
                Command(
                    label=f"{skill.lifecycle}:{skill.name}:sync-check:{hook.name}",
                    argv=(
                        interpreter,
                        PurePosixPath("scripts", hook.name).as_posix(),
                        "--check",
                    ),
                    cwd=skill.absolute_path,
                )
            )
        if found == 0:
            raise DiscoveryError(
                "SOURCE_SKILL_TEST_HOOK_MISSING",
                f"{skill.name}: selected source-backed Skill has no controlled behavior hook",
            )
        commands.append(
            Command(
                label=f"{skill.lifecycle}:{skill.name}:compile",
                argv=(
                    interpreter,
                    "-B",
                    str(root / "tools" / "run_tests.py"),
                    "--compile-tree",
                    skill.relative_path.as_posix(),
                ),
                cwd=root,
            )
        )

    ordered = sorted(commands, key=lambda item: item.label)
    for command in ordered:
        identity = (str(command.cwd.resolve()), command.argv)
        if command.label in labels or identity in identities:
            raise DiscoveryError("TEST_COMMAND_DUPLICATE", "test discovery produced a duplicate command")
        labels.add(command.label)
        identities.add(identity)
    return tuple(ordered)


def _repository_status(root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def _offline_sitecustomize(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=False)
    directory.joinpath("sitecustomize.py").write_text(
        """
import socket

def _blocked(*args, **kwargs):
    raise RuntimeError("NETWORK_DISABLED_BY_VIBE_DFT_TEST_RUNNER")

socket.create_connection = _blocked
socket.getaddrinfo = _blocked
socket.socket.connect = _blocked
socket.socket.connect_ex = _blocked
""".lstrip(),
        encoding="utf-8",
    )


def execute_commands(
    root: Path,
    commands: Iterable[Command],
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> int:
    initial_status = _repository_status(root)
    if initial_status not in (None, ""):
        print("FAIL: repository is dirty before source Skill tests", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="vibe-dft-offline-") as temporary:
        temporary_path = Path(temporary)
        site_path = temporary_path / "python-policy"
        _offline_sitecustomize(site_path)
        environment = dict(os.environ)
        environment[BYTECODE_ENV] = "1"
        environment[OFFLINE_ENV] = "1"
        environment["TMPDIR"] = str(temporary_path / "tmp")
        environment["TEMP"] = environment["TMPDIR"]
        environment["TMP"] = environment["TMPDIR"]
        Path(environment["TMPDIR"]).mkdir()
        existing_pythonpath = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = (
            str(site_path)
            if not existing_pythonpath
            else os.pathsep.join((str(site_path), existing_pythonpath))
        )
        for secret_name in (
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "GITHUB_TOKEN",
            "GH_TOKEN",
            "OPENAI_API_KEY",
            "SSH_AUTH_SOCK",
        ):
            environment.pop(secret_name, None)

        count = 0
        for command in commands:
            count += 1
            print(f"+ [{command.label}]", " ".join(command.argv), flush=True)
            try:
                result = subprocess.run(
                    command.argv,
                    cwd=command.cwd,
                    env=environment,
                    check=False,
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                print(f"FAIL: {command.label} timed out", file=sys.stderr)
                return 2
            except OSError:
                print(f"FAIL: {command.label} could not start", file=sys.stderr)
                return 2
            if result.returncode != 0:
                print(
                    f"FAIL: {command.label} normalized_exit=2 raw_exit={result.returncode}",
                    file=sys.stderr,
                )
                return 2
            current_status = _repository_status(root)
            if current_status not in (None, initial_status):
                print(
                    f"FAIL: {command.label} modified the repository working tree",
                    file=sys.stderr,
                )
                return 2
    print(f"PASS: {count} source Skill offline commands completed")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lifecycle",
        default="development",
        help="comma-separated lifecycle selection; default: development",
    )
    parser.add_argument("--list", action="store_true", help="list commands without executing them")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--root", type=Path, default=repo_root())
    args = parser.parse_args(argv)
    if args.timeout_seconds < 1:
        print("USAGE_ERROR: timeout must be positive", file=sys.stderr)
        return 2
    try:
        lifecycles = _parse_lifecycles(args.lifecycle)
        commands = discover_commands(args.root.resolve(), lifecycles)
    except DiscoveryError as exc:
        print(f"DISCOVERY_ERROR {exc.code}: {exc}", file=sys.stderr)
        return 2
    if args.list:
        for command in commands:
            print(f"{command.label}\t{command.cwd}\t{' '.join(command.argv)}")
        return 0
    return execute_commands(
        args.root.resolve(),
        commands,
        timeout_seconds=args.timeout_seconds,
    )


if __name__ == "__main__":
    raise SystemExit(main())
