#!/usr/bin/env python3
"""Run deterministic maintenance checks for source-backed development Skills.

This runner is deliberately separate from ``tools/run_tests.py``. The active
runner remains the release and routing gate for active Skills; this maintenance
lane only detects regressions in development source trees. It never changes a
Skill lifecycle, installation eligibility, routing state, or claim ceiling.

Controlled hooks are ``tests/test_*.py`` (one unittest discovery run),
``scripts/test_*.py`` (direct script), and ``scripts/{check,sync}_*.py`` only
when the hook declares both a literal argparse ``--check`` option and the
module-level literal ``DEVELOPMENT_MAINTENANCE_CHECK_IS_OFFLINE = True``.
Check hooks are always invoked with ``--check``. Other scripts, native
scientific executables, and unmarked check/sync commands are never executed.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import ast
from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
from typing import Iterable, Mapping

from registry_yaml import RegistryYAMLError, load_yaml_strict


CANONICAL_TEST_HOOK = re.compile(r"^test_[a-z0-9_]+\.py$")
CANONICAL_CHECK_HOOK = re.compile(r"^(?:check|sync)_[a-z0-9_]+\.py$")
BYTECODE_ENV = "PYTHONDONTWRITEBYTECODE"
MAINTENANCE_ENV = "VIBE_DFT_DEVELOPMENT_MAINTENANCE"
OFFLINE_CHECK_MARKER = "DEVELOPMENT_MAINTENANCE_CHECK_IS_OFFLINE"
RUNNER_SCRIPT = Path(__file__).resolve()
FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "MDAnalysis",
        "aiohttp",
        "ase",
        "asyncssh",
        "asyncio",
        "catmap",
        "cclib",
        "ctypes",
        "deepmd",
        "dpdata",
        "fabric",
        "fairchem",
        "ftplib",
        "gpyumd",
        "grpc",
        "gromacs",
        "http",
        "lammps",
        "lobsterpy",
        "mace",
        "mdtraj",
        "nequip",
        "ovito",
        "paramiko",
        "pexpect",
        "phonopy",
        "pymatgen",
        "rdkit",
        "requests",
        "smtplib",
        "socket",
        "spglib",
        "telnetlib",
        "torch",
        "urllib",
        "webbrowser",
        "websockets",
        "xmlrpc",
    }
)
SUBPROCESS_CALLS = frozenset(
    {
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.Popen",
        "subprocess.run",
    }
)
FORBIDDEN_PROCESS_CALLS = frozenset({"os.popen", "os.system"})

# A reviewed allowlist is required because a filename alone cannot prove that a
# test is local, offline, or free of native scientific execution. New matching
# hooks are reported as skipped until this table is updated in a reviewed
# change. Paths are relative to the corresponding Skill source directory.
REVIEWED_MAINTENANCE_HOOKS: Mapping[str, frozenset[str]] = {
    "catmap-microkinetics": frozenset(
        {
            "scripts/test_source_pack_metadata.py",
            "tests/test_catmap_catalog.py",
            "tests/test_catmap_guard.py",
        }
    ),
    "deepmd-rigorous-workflows": frozenset(
        {
            "scripts/test_source_pack_metadata.py",
            "tests/test_deepmd_guard.py",
        }
    ),
    "dft-hpc-execution": frozenset(
        {"tests/test_hpc_execution_cli.py"}
    ),
    "dft-project-orchestrator": frozenset(
        {"tests/test_orchestrator_cli.py"}
    ),
    "dft-reporting": frozenset(
        {"tests/test_reporting_cli.py"}
    ),
    "dft-review-response": frozenset(
        {"tests/test_review_response_cli.py"}
    ),
    "dft-structure-preparation": frozenset(
        {
            "scripts/test_source_pack_metadata.py",
            "tests/test_heterostructure_prescreen_contract.py",
            "tests/test_redteam_mutations.py",
            "tests/test_structure_prepare.py",
        }
    ),
    "gaussian-rigorous-calculations": frozenset(
        {
            "tests/test_gaussian_guard.py",
            "tests/test_official_document_seed.py",
        }
    ),
    "gpumd-rigorous-simulations": frozenset(
        {
            "scripts/test_source_pack_metadata.py",
            "tests/test_gpumd_guard.py",
        }
    ),
    "gromacs-rigorous-simulations": frozenset(
        {
            "scripts/test_source_pack_metadata.py",
            "tests/test_gromacs_guard.py",
            "tests/test_gromacs_manual.py",
        }
    ),
    "lammps-rigorous-simulations": frozenset(
        {
            "scripts/test_source_pack_metadata.py",
            "tests/test_lammps_guard.py",
            "tests/test_lammps_manual.py",
        }
    ),
    "lasp-rigorous-simulations": frozenset(
        {
            "tests/test_lasp_evidence_guard.py",
            "tests/test_official_document_seed.py",
        }
    ),
    "literature-to-dft-plan": frozenset(
        {"tests/test_literature_plan_cli.py"}
    ),
    "lobster-bonding-analysis": frozenset(
        {
            "tests/test_lobster_catalog.py",
            "tests/test_lobster_guard.py",
            "tests/test_official_document_seed.py",
        }
    ),
    "ml-potential-workflows": frozenset(
        {"tests/test_mlp_guard.py"}
    ),
    "multiwfn-wavefunction-analysis": frozenset(
        {
            "scripts/test_source_pack_metadata.py",
            "tests/test_multiwfn_catalog.py",
            "tests/test_multiwfn_guard.py",
        }
    ),
    "ovito-atomistic-analysis": frozenset(
        {
            "scripts/test_source_pack_metadata.py",
            "tests/test_ovito_analysis.py",
            "tests/test_redteam_boundaries.py",
        }
    ),
    "phonopy-rigorous-workflows": frozenset(
        {
            "scripts/test_source_pack_metadata.py",
            "tests/test_phonopy_catalog.py",
            "tests/test_phonopy_guard.py",
        }
    ),
    "vaspkit-postprocess": frozenset(
        {
            "scripts/test_source_pack_metadata.py",
            "tests/test_vaspkit_catalog.py",
            "tests/test_vaspkit_guard.py",
        }
    ),
}


class DiscoveryError(ValueError):
    """A stable, fail-closed development test-discovery error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class DevelopmentSkill:
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


@dataclass(frozen=True)
class MaintenancePlan:
    commands: tuple[Command, ...]
    skipped: tuple[str, ...]
    skill_count: int
    reviewed_hook_count: int


def _safe_relative_path(value: object) -> PurePosixPath | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path


def compile_python_tree(root: Path, relative_value: str) -> int:
    """Compile a source tree in memory without writing bytecode."""

    relative = _safe_relative_path(relative_value)
    if relative is None:
        print("COMPILE_ERROR SOURCE_PATH_INVALID", file=sys.stderr)
        return 2
    source_root = root.joinpath(*relative.parts)
    if source_root.is_symlink() or not source_root.is_dir():
        print("COMPILE_ERROR SOURCE_TREE_INVALID", file=sys.stderr)
        return 2
    for path in sorted(
        source_root.rglob("*.py"),
        key=lambda item: item.relative_to(source_root).as_posix(),
    ):
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


def load_development_skills(root: Path) -> tuple[DevelopmentSkill, ...]:
    """Load only source-backed development Skills from the canonical registry."""

    registry_path = root / "registry" / "skill-registry.yaml"
    try:
        registry = load_yaml_strict(registry_path)
    except (OSError, UnicodeError, RegistryYAMLError) as exc:
        raise DiscoveryError(
            "REGISTRY_UNREADABLE",
            "the Skill registry cannot be read",
        ) from exc
    if not isinstance(registry, dict) or registry.get("schema_version") != "1.0":
        raise DiscoveryError(
            "REGISTRY_SCHEMA_INVALID",
            "the Skill registry has an unsupported schema",
        )
    skills = registry.get("skills")
    if not isinstance(skills, dict) or not skills:
        raise DiscoveryError(
            "REGISTRY_SKILLS_INVALID",
            "the Skill registry has no skills mapping",
        )
    if any(
        not isinstance(name, str) or not isinstance(specification, dict)
        for name, specification in skills.items()
    ):
        raise DiscoveryError(
            "REGISTRY_ENTRY_INVALID",
            "a Skill registry entry is malformed",
        )

    development: list[DevelopmentSkill] = []
    resolved_paths: set[Path] = set()
    for name in sorted(skills):
        specification = skills[name]
        if specification.get("lifecycle") != "development":
            continue
        expected = PurePosixPath("skills", name)
        relative = _safe_relative_path(specification.get("path"))
        if relative != expected:
            raise DiscoveryError(
                "DEVELOPMENT_SKILL_PATH_INVALID",
                "a development Skill does not use its canonical source path",
            )
        absolute = root.joinpath(*relative.parts)
        if (
            absolute.is_symlink()
            or not absolute.is_dir()
            or not absolute.joinpath("SKILL.md").is_file()
        ):
            raise DiscoveryError(
                "DEVELOPMENT_SKILL_SOURCE_MISSING",
                "a development Skill source is missing, aliased, or incomplete",
            )
        resolved = absolute.resolve()
        if resolved in resolved_paths:
            raise DiscoveryError(
                "DEVELOPMENT_SKILL_PATH_DUPLICATE",
                "more than one development Skill resolves to the same source path",
            )
        resolved_paths.add(resolved)
        development.append(
            DevelopmentSkill(
                name=name,
                relative_path=relative,
                absolute_path=absolute,
            )
        )
    return tuple(development)


def _canonical_hook_files(
    directory: Path,
    prefix: str,
    pattern: re.Pattern[str],
) -> tuple[Path, ...]:
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        raise DiscoveryError(
            "TEST_HOOK_DIRECTORY_INVALID",
            "a test-hook directory is aliased or not a directory",
        )
    candidates = sorted(directory.glob(f"{prefix}*.py"), key=lambda item: item.name)
    hooks: list[Path] = []
    for path in candidates:
        if path.is_symlink() or not path.is_file():
            raise DiscoveryError(
                "TEST_HOOK_FILE_INVALID",
                "a discovered test hook is aliased or not a file",
            )
        if not pattern.fullmatch(path.name):
            raise DiscoveryError(
                "TEST_HOOK_NAME_INVALID",
                "a discovered test hook has a noncanonical filename",
            )
        hooks.append(path)
    return tuple(hooks)


def _parse_check_hook(path: Path) -> ast.Module:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise DiscoveryError(
            "CHECK_HOOK_UNREADABLE",
            "a check hook cannot be parsed",
        ) from exc


def _qualified_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _is_sys_executable_argv(node: ast.AST) -> bool:
    if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
        return False
    return _qualified_name(node.elts[0]) == "sys.executable"


def _validate_static_maintenance_safety(path: Path, tree: ast.Module) -> None:
    """Reject obvious network, provider-import, shell, and native process paths.

    The reviewed allowlist remains the human attestation for local temporary
    writes. This bounded AST gate ensures an allowlisted hook cannot silently
    gain a direct network/provider import or launch an external executable.
    Python subprocesses are permitted only when their literal argv begins with
    ``sys.executable``; the reviewed tests use that route for isolated FIFO and
    local CLI boundary checks.
    """

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    raise DiscoveryError(
                        "MAINTENANCE_HOOK_IMPORT_FORBIDDEN",
                        "a reviewed maintenance hook imports a network or provider module",
                    )
                if root in {"os", "subprocess"} and alias.asname is not None:
                    raise DiscoveryError(
                        "MAINTENANCE_HOOK_PROCESS_ALIAS_FORBIDDEN",
                        "a reviewed maintenance hook aliases a process-capable module",
                    )
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                raise DiscoveryError(
                    "MAINTENANCE_HOOK_IMPORT_FORBIDDEN",
                    "a reviewed maintenance hook imports a network or provider module",
                )
            if root == "subprocess":
                raise DiscoveryError(
                    "MAINTENANCE_HOOK_PROCESS_ALIAS_FORBIDDEN",
                    "a reviewed maintenance hook imports subprocess call aliases",
                )
            if root == "os" and any(
                alias.name in {"popen", "system"}
                or alias.name.startswith(("exec", "spawn", "posix_spawn"))
                for alias in node.names
            ):
                raise DiscoveryError(
                    "MAINTENANCE_HOOK_PROCESS_ALIAS_FORBIDDEN",
                    "a reviewed maintenance hook imports process call aliases",
                )
        elif isinstance(node, ast.Call):
            name = _qualified_name(node.func)
            if name in FORBIDDEN_PROCESS_CALLS or name.startswith(
                ("os.exec", "os.spawn", "os.posix_spawn")
            ):
                raise DiscoveryError(
                    "MAINTENANCE_HOOK_EXTERNAL_PROCESS_FORBIDDEN",
                    "a reviewed maintenance hook launches an external process",
                )
            if name in SUBPROCESS_CALLS:
                if not node.args or not _is_sys_executable_argv(node.args[0]):
                    raise DiscoveryError(
                        "MAINTENANCE_HOOK_EXTERNAL_PROCESS_FORBIDDEN",
                        "a reviewed maintenance hook has a non-Python subprocess route",
                    )
                shell_values = [
                    keyword.value
                    for keyword in node.keywords
                    if keyword.arg == "shell"
                ]
                if any(
                    not (
                        isinstance(value, ast.Constant)
                        and value.value is False
                    )
                    for value in shell_values
                ):
                    raise DiscoveryError(
                        "MAINTENANCE_HOOK_SHELL_FORBIDDEN",
                        "a reviewed maintenance hook enables a subprocess shell",
                    )


def _declares_check_flag(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument" or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and first.value == "--check":
            return True
    return False


def _declares_offline_check(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == OFFLINE_CHECK_MARKER
                and isinstance(node.value, ast.Constant)
                and node.value.value is True
            ):
                return True
        if isinstance(node, ast.AnnAssign):
            if (
                isinstance(node.target, ast.Name)
                and node.target.id == OFFLINE_CHECK_MARKER
                and isinstance(node.value, ast.Constant)
                and node.value.value is True
            ):
                return True
    return False


def _validate_check_hook(path: Path) -> None:
    tree = _parse_check_hook(path)
    _validate_static_maintenance_safety(path, tree)
    if not _declares_check_flag(tree):
        raise DiscoveryError(
            "CHECK_HOOK_FLAG_MISSING",
            "a development check hook does not declare the required --check mode",
        )
    if not _declares_offline_check(tree):
        raise DiscoveryError(
            "CHECK_HOOK_OFFLINE_MARKER_MISSING",
            "a development check hook does not declare the offline maintenance contract",
        )


def _reviewed_hook_path(value: str) -> PurePosixPath | None:
    relative = _safe_relative_path(value)
    if relative is None or len(relative.parts) != 2:
        return None
    directory, filename = relative.parts
    if directory == "tests" and CANONICAL_TEST_HOOK.fullmatch(filename):
        return relative
    if directory == "scripts" and (
        CANONICAL_TEST_HOOK.fullmatch(filename)
        or CANONICAL_CHECK_HOOK.fullmatch(filename)
    ):
        return relative
    return None


def _validate_reviewed_hooks(
    skills: tuple[DevelopmentSkill, ...],
    reviewed_hooks: Mapping[str, frozenset[str]],
) -> dict[str, frozenset[PurePosixPath]]:
    skill_by_name = {skill.name: skill for skill in skills}
    unexpected = sorted(set(reviewed_hooks) - set(skill_by_name))
    if unexpected:
        raise DiscoveryError(
            "MAINTENANCE_ALLOWLIST_SKILL_INVALID",
            "the maintenance allowlist names a non-development Skill",
        )

    validated: dict[str, frozenset[PurePosixPath]] = {}
    for skill_name in sorted(reviewed_hooks):
        skill = skill_by_name[skill_name]
        paths: set[PurePosixPath] = set()
        for value in sorted(reviewed_hooks[skill_name]):
            relative = _reviewed_hook_path(value)
            if relative is None:
                raise DiscoveryError(
                    "MAINTENANCE_ALLOWLIST_PATH_INVALID",
                    "the maintenance allowlist contains a noncanonical hook path",
                )
            absolute = skill.absolute_path.joinpath(*relative.parts)
            if absolute.is_symlink() or not absolute.is_file():
                raise DiscoveryError(
                    "MAINTENANCE_ALLOWLIST_ENTRY_MISSING",
                    "a reviewed maintenance hook is missing or aliased",
                )
            try:
                tree = ast.parse(absolute.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, SyntaxError) as exc:
                raise DiscoveryError(
                    "MAINTENANCE_HOOK_UNREADABLE",
                    "a reviewed maintenance hook cannot be parsed",
                ) from exc
            _validate_static_maintenance_safety(absolute, tree)
            paths.add(relative)
        validated[skill_name] = frozenset(paths)
    return validated


def ensure_unique_commands(commands: Iterable[Command]) -> tuple[Command, ...]:
    result: list[Command] = []
    identities: set[tuple[str, tuple[str, ...]]] = set()
    labels: set[str] = set()
    for command in commands:
        if command.identity in identities or command.label in labels:
            raise DiscoveryError(
                "TEST_COMMAND_DUPLICATE",
                "development test discovery produced a duplicate command",
            )
        identities.add(command.identity)
        labels.add(command.label)
        result.append(command)
    return tuple(result)


def discover_maintenance_plan(
    root: Path,
    python: str,
    *,
    skills: tuple[DevelopmentSkill, ...] | None = None,
    reviewed_hooks: Mapping[str, frozenset[str]] = REVIEWED_MAINTENANCE_HOOKS,
) -> MaintenancePlan:
    selected_skills = skills if skills is not None else load_development_skills(root)
    reviewed = _validate_reviewed_hooks(selected_skills, reviewed_hooks)
    commands: list[Command] = []
    skipped: list[str] = []
    reviewed_hook_count = 0
    for skill in selected_skills:
        relative = skill.relative_path.as_posix()
        allowed = reviewed.get(skill.name, frozenset())
        discovered_hook_count = 0

        commands.append(
            Command(
                label=f"development:{skill.name}:compile:{relative}",
                argv=(python, "-B", str(RUNNER_SCRIPT), "--compile-tree", relative),
                cwd=root,
            )
        )

        tests_dir = skill.absolute_path / "tests"
        unittest_hooks = _canonical_hook_files(
            tests_dir,
            "test_",
            CANONICAL_TEST_HOOK,
        )
        for hook in unittest_hooks:
            discovered_hook_count += 1
            hook_relative = PurePosixPath("tests", hook.name)
            if hook_relative not in allowed:
                skipped.append(
                    f"development:{skill.name}:unreviewed-hook:{hook_relative.as_posix()}"
                )
                continue
            reviewed_hook_count += 1
            commands.append(
                Command(
                    label=f"development:{skill.name}:unittest:{hook.name}",
                    argv=(
                        python,
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        hook.name,
                        "-v",
                    ),
                    cwd=skill.absolute_path,
                )
            )

        scripts_dir = skill.absolute_path / "scripts"
        script_tests = _canonical_hook_files(
            scripts_dir,
            "test_",
            CANONICAL_TEST_HOOK,
        )
        for hook in script_tests:
            discovered_hook_count += 1
            hook_relative = PurePosixPath("scripts", hook.name)
            if hook_relative not in allowed:
                skipped.append(
                    f"development:{skill.name}:unreviewed-hook:{hook_relative.as_posix()}"
                )
                continue
            reviewed_hook_count += 1
            commands.append(
                Command(
                    label=f"development:{skill.name}:script-test:{hook.name}",
                    argv=(python, PurePosixPath("scripts", hook.name).as_posix()),
                    cwd=skill.absolute_path,
                )
            )

        for prefix in ("check_", "sync_"):
            check_hooks = _canonical_hook_files(
                scripts_dir,
                prefix,
                CANONICAL_CHECK_HOOK,
            )
            for hook in check_hooks:
                discovered_hook_count += 1
                hook_relative = PurePosixPath("scripts", hook.name)
                if hook_relative not in allowed:
                    skipped.append(
                        f"development:{skill.name}:unreviewed-hook:{hook_relative.as_posix()}"
                    )
                    continue
                _validate_check_hook(hook)
                reviewed_hook_count += 1
                commands.append(
                    Command(
                        label=f"development:{skill.name}:check:{hook.name}",
                        argv=(
                            python,
                            PurePosixPath("scripts", hook.name).as_posix(),
                            "--check",
                        ),
                        cwd=skill.absolute_path,
                    )
                )

        if discovered_hook_count == 0:
            skipped.append(
                f"development:{skill.name}:no-controlled-behavioral-hook"
            )

    kind_order = {"compile": 0, "unittest": 1, "script-test": 2, "check": 3}

    def key(command: Command) -> tuple[str, int, str]:
        _, skill_name, kind, detail = command.label.split(":", 3)
        return (skill_name, kind_order[kind], detail)

    ordered_commands = ensure_unique_commands(sorted(commands, key=key))
    return MaintenancePlan(
        commands=ordered_commands,
        skipped=tuple(sorted(skipped)),
        skill_count=len(selected_skills),
        reviewed_hook_count=reviewed_hook_count,
    )


def discover_skill_commands(
    root: Path,
    python: str,
    *,
    skills: tuple[DevelopmentSkill, ...] | None = None,
    reviewed_hooks: Mapping[str, frozenset[str]] = REVIEWED_MAINTENANCE_HOOKS,
) -> tuple[Command, ...]:
    """Compatibility helper returning only reviewed executable commands."""

    return discover_maintenance_plan(
        root,
        python,
        skills=skills,
        reviewed_hooks=reviewed_hooks,
    ).commands


def child_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment[BYTECODE_ENV] = "1"
    environment[MAINTENANCE_ENV] = "1"
    return environment


def execute_commands(commands: Iterable[Command]) -> int:
    environment = child_environment()
    if (
        environment.get(BYTECODE_ENV) != "1"
        or environment.get(MAINTENANCE_ENV) != "1"
    ):
        print(
            "FAIL: development runner normalized_exit=2 raw_exit=environment-policy",
            file=sys.stderr,
        )
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
            print(
                f"FAIL: {command.label} normalized_exit=2 raw_exit=not-started",
                file=sys.stderr,
            )
            return 2
        if result.returncode != 0:
            print(
                f"FAIL: {command.label} normalized_exit=2 raw_exit={result.returncode}",
                file=sys.stderr,
            )
            return 2
    return 0


def render_plan(root: Path, plan: MaintenancePlan) -> None:
    for command in plan.commands:
        try:
            relative_cwd = command.cwd.resolve().relative_to(root.resolve()).as_posix()
        except ValueError as exc:
            raise DiscoveryError(
                "TEST_COMMAND_CWD_INVALID",
                "a maintenance command escapes the repository root",
            ) from exc
        display_argv = [
            "python" if value == sys.executable else value
            for value in command.argv
        ]
        display_argv = [
            "tools/run_development_tests.py"
            if value == str(RUNNER_SCRIPT)
            else value
            for value in display_argv
        ]
        print(
            f"LIST: [{command.label}] "
            f"cwd={relative_cwd or '.'} argv={shlex.join(display_argv)}"
        )
    for item in plan.skipped:
        print(f"SKIP: {item}")
    print(
        "PLAN: "
        f"skills={plan.skill_count} "
        f"reviewed_hooks={plan.reviewed_hook_count} "
        f"commands={len(plan.commands)} "
        f"skipped={len(plan.skipped)}"
    )


def main(root: Path | None = None, argv: tuple[str, ...] = ()) -> int:
    selected_root = root or Path(__file__).resolve().parents[1]
    if len(argv) == 2 and argv[0] == "--compile-tree":
        return compile_python_tree(root or Path.cwd(), argv[1])
    list_only = argv == ("--list",)
    if argv and not list_only:
        print("USAGE_ERROR: unsupported development runner arguments", file=sys.stderr)
        return 2
    try:
        skills = load_development_skills(selected_root)
        plan = discover_maintenance_plan(
            selected_root,
            sys.executable,
            skills=skills,
        )
    except DiscoveryError as exc:
        print(f"DISCOVERY_ERROR {exc.code}: {exc}", file=sys.stderr)
        return 2
    if list_only:
        try:
            render_plan(selected_root, plan)
        except DiscoveryError as exc:
            print(f"DISCOVERY_ERROR {exc.code}: {exc}", file=sys.stderr)
            return 2
        return 0
    for item in plan.skipped:
        print(f"SKIP: {item}", flush=True)
    result = execute_commands(plan.commands)
    if result != 0:
        return result
    print(
        "PASS: "
        f"{len(skills)} source-backed development Skills completed "
        f"{len(plan.commands)} deterministic maintenance commands; "
        f"reviewed_hooks={plan.reviewed_hook_count}; "
        f"skipped={len(plan.skipped)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(argv=tuple(sys.argv[1:])))
