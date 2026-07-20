#!/usr/bin/env python3
"""Validate one development-to-active promotion against immutable Git objects."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Any, Iterable, Iterator, Sequence

from registry_yaml import RegistryYAMLError, loads_yaml_strict
import strict_json
import validate_contract
from skill_registry import TREE_HASH_DOMAIN


MAX_GIT_FILE_BYTES = 16 * 1024 * 1024
MATURITY_ORDER = {
    "design-only": 0,
    "synthetic-validated": 1,
    "format-fixture-validated": 2,
    "real-artifact-validated": 3,
    "tool-integration-validated": 4,
}
CLAIM_ORDER = {
    "no_positive_claim": 0,
    "documented_behavior_only": 1,
    "input_gates_only": 2,
    "technical_run_gates_only": 3,
    "numerical_candidate_only": 4,
    "eligible_for_expert_review": 5,
}
MATURITY_MAX_CLAIM = {
    "design-only": "no_positive_claim",
    "synthetic-validated": "documented_behavior_only",
    "format-fixture-validated": "technical_run_gates_only",
    "real-artifact-validated": "numerical_candidate_only",
    "tool-integration-validated": "eligible_for_expert_review",
}


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    location: str
    message: str

    def render(self) -> str:
        return f"{self.code}\t{self.location}\t{self.message}"


@dataclass(frozen=True)
class GitFile:
    path: str
    raw: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.raw).hexdigest()


class GitError(ValueError):
    pass


class GitRepository:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        probe = self._run(["rev-parse", "--git-dir"])
        if probe.returncode != 0:
            raise GitError("repository root is not a readable Git work tree")

    def _run(self, arguments: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def resolve_commit(self, value: object, label: str) -> str:
        if not isinstance(value, str) or len(value) not in (40, 64):
            raise GitError(f"{label}: commit ID must be a 40- or 64-character hex string")
        completed = self._run(["rev-parse", "--verify", f"{value}^{{commit}}"])
        if completed.returncode != 0:
            raise GitError(f"{label}: commit does not resolve")
        resolved = completed.stdout.decode("ascii", errors="strict").strip()
        if resolved != value:
            raise GitError(f"{label}: commit must be canonical and exact")
        return resolved

    def is_ancestor(self, base: str, candidate: str) -> bool:
        return self._run(["merge-base", "--is-ancestor", base, candidate]).returncode == 0

    def file(self, commit: str, path_text: object) -> GitFile:
        path = _safe_path(path_text)
        if path is None:
            raise GitError(f"unsafe repository path: {path_text!r}")
        completed = self._run(["show", f"{commit}:{path}"])
        if completed.returncode != 0:
            raise GitError(f"{path}: file does not exist at {commit}")
        if len(completed.stdout) > MAX_GIT_FILE_BYTES:
            raise GitError(f"{path}: file exceeds the validation size limit")
        return GitFile(path=path, raw=completed.stdout)

    def json_file(self, commit: str, path_text: object) -> tuple[GitFile, dict[str, Any]]:
        item = self.file(commit, path_text)
        try:
            value = strict_json.loads_object(item.raw, item.path, max_bytes=MAX_GIT_FILE_BYTES)
        except strict_json.StrictJSONError as exc:
            raise GitError(f"{item.path}: strict JSON invalid: {exc}") from exc
        return item, value

    def yaml_file(self, commit: str, path_text: object) -> tuple[GitFile, dict[str, Any]]:
        item = self.file(commit, path_text)
        try:
            text = item.raw.decode("utf-8", errors="strict")
            value = loads_yaml_strict(text, item.path)
        except (UnicodeDecodeError, RegistryYAMLError) as exc:
            raise GitError(f"{item.path}: strict YAML invalid: {exc}") from exc
        return item, value

    def diff_paths(self, base: str, candidate: str) -> tuple[str, ...]:
        completed = self._run(
            ["diff", "--name-only", "-z", "--diff-filter=ACMRT", base, candidate, "--"]
        )
        if completed.returncode != 0:
            raise GitError("candidate diff cannot be enumerated")
        paths = []
        for raw in completed.stdout.split(b"\0"):
            if not raw:
                continue
            text = raw.decode("utf-8", errors="strict")
            safe = _safe_path(text)
            if safe is None:
                raise GitError("candidate diff contains an unsafe path")
            paths.append(safe)
        return tuple(sorted(set(paths)))

    def tree_paths(self, commit: str, prefix: str) -> tuple[str, ...]:
        safe_prefix = _safe_path(prefix)
        if safe_prefix is None:
            raise GitError("unsafe tree prefix")
        completed = self._run(["ls-tree", "-r", "--name-only", "-z", commit, "--", safe_prefix])
        if completed.returncode != 0:
            raise GitError(f"cannot enumerate source tree {safe_prefix}")
        paths = []
        for raw in completed.stdout.split(b"\0"):
            if raw:
                paths.append(raw.decode("utf-8", errors="strict"))
        return tuple(sorted(paths))

    def source_tree_sha256(self, commit: str, prefix: str) -> str:
        prefix_path = PurePosixPath(prefix)
        files: list[tuple[str, bytes]] = []
        for full_path in self.tree_paths(commit, prefix):
            relative = PurePosixPath(full_path).relative_to(prefix_path).as_posix()
            if any(part in {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"} for part in PurePosixPath(relative).parts):
                continue
            if PurePosixPath(relative).name in {".coverage", ".DS_Store"}:
                continue
            if PurePosixPath(relative).suffix.lower() in {".pyc", ".pyo", ".pyd"}:
                continue
            files.append((relative, self.file(commit, full_path).raw))
        if not files:
            raise GitError(f"{prefix}: source tree contains no regular Git blobs")
        digest = hashlib.sha256()
        digest.update(TREE_HASH_DOMAIN)
        for relative, raw in sorted(files):
            path_raw = relative.encode("utf-8")
            digest.update(len(path_raw).to_bytes(8, "big") + path_raw)
            digest.update(len(raw).to_bytes(8, "big") + raw)
        return digest.hexdigest()


def _safe_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def _iter_dicts(value: object, path: tuple[object, ...] = ()) -> Iterator[tuple[tuple[object, ...], dict[str, Any]]]:
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from _iter_dicts(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_dicts(child, (*path, index))


def _pointer(path: Iterable[object]) -> str:
    parts = tuple(path)
    return "<root>" if not parts else "/" + "/".join(str(item) for item in parts)


def _record_id(data: dict[str, Any], contract: validate_contract.ContractSchema) -> str | None:
    field = contract.record_id_field
    value = data.get(field) if field else None
    return value if isinstance(value, str) else None


def _active_set(registry: dict[str, Any]) -> set[str]:
    skills = registry.get("skills")
    if not isinstance(skills, dict):
        return set()
    return {
        name
        for name, specification in skills.items()
        if isinstance(name, str)
        and isinstance(specification, dict)
        and specification.get("lifecycle") == "active"
    }


def _find_skill(registry: dict[str, Any], skill_id: str) -> dict[str, Any] | None:
    skills = registry.get("skills")
    if not isinstance(skills, dict):
        return None
    value = skills.get(skill_id)
    return value if isinstance(value, dict) else None


def _file_ref_findings(
    repo: GitRepository,
    candidate: str,
    value: object,
    *,
    prefix: tuple[object, ...] = (),
) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for path, node in _iter_dicts(value, prefix):
        if set(node).issuperset({"path", "sha256"}):
            path_text = node.get("path")
            expected = node.get("sha256")
            if path_text is None:
                continue
            key = (str(path_text), str(expected))
            if key in seen:
                continue
            seen.add(key)
            try:
                item = repo.file(candidate, path_text)
            except GitError as exc:
                findings.append(Finding("PROMOTION_FILE_REF_MISSING", _pointer(path), str(exc)))
                continue
            if expected != item.sha256:
                findings.append(
                    Finding(
                        "PROMOTION_FILE_REF_HASH_MISMATCH",
                        _pointer(path),
                        f"{item.path}: declared SHA-256 does not match candidate bytes",
                    )
                )
    return findings


def _build_record_index(
    repo: GitRepository,
    candidate: str,
    paths: Iterable[str],
    contracts_dir: Path,
) -> tuple[dict[tuple[str, str, str], tuple[str, str]], list[Finding]]:
    index: dict[tuple[str, str, str], tuple[str, str]] = {}
    findings: list[Finding] = []
    catalog = validate_contract.load_catalog(contracts_dir)
    for path in sorted(set(paths)):
        if not path.endswith(".json"):
            continue
        try:
            item, data = repo.json_file(candidate, path)
        except GitError:
            continue
        name = data.get("contract_name")
        version = data.get("schema_version")
        if not isinstance(name, str) or not isinstance(version, str):
            continue
        try:
            contract = catalog.resolve(f"{name}@{version}")
        except validate_contract.ContractSelectionError:
            continue
        record_id = _record_id(data, contract)
        if record_id is None:
            continue
        key = (name, version, record_id)
        previous = index.get(key)
        value = (item.path, item.sha256)
        if previous is not None and previous != value:
            findings.append(
                Finding(
                    "PROMOTION_RECORD_ID_AMBIGUOUS",
                    item.path,
                    f"record identity {key!r} resolves to more than one candidate file",
                )
            )
        else:
            index[key] = value
    return index, findings


def _record_ref_findings(
    value: object,
    index: dict[tuple[str, str, str], tuple[str, str]],
    *,
    prefix: tuple[object, ...] = (),
) -> list[Finding]:
    findings: list[Finding] = []
    for path, node in _iter_dicts(value, prefix):
        if not set(node).issuperset({"contract_name", "schema_version", "record_id", "sha256"}):
            continue
        key = (node.get("contract_name"), node.get("schema_version"), node.get("record_id"))
        if not all(isinstance(item, str) for item in key):
            continue
        resolved = index.get(key)  # type: ignore[arg-type]
        if resolved is None:
            findings.append(
                Finding(
                    "PROMOTION_RECORD_REF_UNRESOLVED",
                    _pointer(path),
                    f"record reference {key!r} does not resolve in candidate evidence",
                )
            )
        elif resolved[1] != node.get("sha256"):
            findings.append(
                Finding(
                    "PROMOTION_RECORD_REF_HASH_MISMATCH",
                    _pointer(path),
                    f"record reference {key!r} SHA-256 does not match {resolved[0]}",
                )
            )
    return findings


def _schema_findings(
    kind: str,
    data: dict[str, Any],
    contracts_dir: Path,
    location: str,
) -> list[Finding]:
    return [
        Finding("PROMOTION_SCHEMA_INVALID", location, error)
        for error in validate_contract.validation_errors(kind, data, contracts_dir)
    ]


def _maturity_findings(
    data: dict[str, Any],
    skill_id: str,
    index: dict[tuple[str, str, str], tuple[str, str]],
) -> list[Finding]:
    findings: list[Finding] = []
    if data.get("skill_id") != skill_id:
        findings.append(
            Finding("PROMOTION_MATURITY_SKILL_MISMATCH", "task_maturity_catalog", "skill_id differs from promotion subject")
        )
    routes = data.get("routes")
    if not isinstance(routes, list):
        return findings
    route_map: dict[str, dict[str, Any]] = {}
    for index_value, route in enumerate(routes):
        if not isinstance(route, dict) or not isinstance(route.get("route_id"), str):
            continue
        route_id = route["route_id"]
        if route_id in route_map:
            findings.append(Finding("PROMOTION_MATURITY_ROUTE_DUPLICATE", f"routes/{index_value}", route_id))
        route_map[route_id] = route
        axes = [
            route.get("invocation_maturity"),
            route.get("parser_maturity"),
            route.get("scientific_validation_maturity"),
        ]
        if all(axis in MATURITY_ORDER for axis in axes):
            computed = min(axes, key=lambda item: MATURITY_ORDER[str(item)])
            overall = route.get("overall_maturity")
            if not isinstance(overall, dict) or overall.get("computed") != computed or overall.get("declared") != computed:
                findings.append(
                    Finding(
                        "PROMOTION_MATURITY_COMPUTED_MISMATCH",
                        f"routes/{index_value}/overall_maturity",
                        f"expected both declared and computed to equal {computed}",
                    )
                )
            ceiling = route.get("claim_ceiling")
            maximum = MATURITY_MAX_CLAIM[str(computed)]
            if ceiling in CLAIM_ORDER and CLAIM_ORDER[str(ceiling)] > CLAIM_ORDER[maximum]:
                findings.append(
                    Finding(
                        "PROMOTION_MATURITY_CLAIM_OVERSTATED",
                        f"routes/{index_value}/claim_ceiling",
                        f"{computed} caps claims at {maximum}",
                    )
                )
    graph: dict[str, str | None] = {}
    for route_id, route in route_map.items():
        parent = route.get("parent_route")
        if isinstance(parent, dict) and parent.get("scope") == "catalog":
            parent_id = parent.get("route_id")
            if not isinstance(parent_id, str) or parent_id not in route_map:
                findings.append(Finding("PROMOTION_MATURITY_PARENT_MISSING", route_id, str(parent_id)))
                graph[route_id] = None
            else:
                graph[route_id] = parent_id
        else:
            graph[route_id] = None
    for start in graph:
        seen: set[str] = set()
        current: str | None = start
        while current is not None:
            if current in seen:
                findings.append(Finding("PROMOTION_MATURITY_PARENT_CYCLE", start, current))
                break
            seen.add(current)
            current = graph.get(current)
    findings.extend(_record_ref_findings(data, index, prefix=("task_maturity_catalog",)))
    return findings


def validate_promotion(
    root: Path,
    promotion_path: Path,
    *,
    contracts_dir: Path | None = None,
) -> tuple[list[Finding], dict[str, Any]]:
    selected_root = root.resolve()
    selected_contracts = (contracts_dir or selected_root / "contracts").resolve()
    findings: list[Finding] = []
    try:
        raw = promotion_path.read_bytes()
        promotion = strict_json.loads_object(raw, promotion_path.name, max_bytes=MAX_GIT_FILE_BYTES)
    except (OSError, strict_json.StrictJSONError) as exc:
        return [Finding("PROMOTION_INPUT_INVALID", str(promotion_path), str(exc))], {}
    findings.extend(_schema_findings("promotion-delta@1.0", promotion, selected_contracts, "promotion"))
    try:
        repo = GitRepository(selected_root)
        base = repo.resolve_commit(promotion.get("base_commit"), "base_commit")
        candidate = repo.resolve_commit(promotion.get("candidate_commit"), "candidate_commit")
    except GitError as exc:
        return sorted(set(findings + [Finding("PROMOTION_COMMIT_INVALID", "commits", str(exc))])), {}
    if base == candidate or not repo.is_ancestor(base, candidate):
        findings.append(Finding("PROMOTION_COMMIT_ORDER_INVALID", "commits", "base must be a strict ancestor of candidate"))

    try:
        base_registry_file, base_registry = repo.yaml_file(base, "registry/skill-registry.yaml")
        candidate_registry_file, candidate_registry = repo.yaml_file(candidate, "registry/skill-registry.yaml")
    except GitError as exc:
        findings.append(Finding("PROMOTION_SKILL_REGISTRY_INVALID", "registry/skill-registry.yaml", str(exc)))
        return sorted(set(findings)), {}
    if promotion.get("base_registry_sha256") != base_registry_file.sha256:
        findings.append(Finding("PROMOTION_BASE_REGISTRY_HASH_MISMATCH", "base_registry_sha256", "does not match base commit bytes"))

    skill_id = promotion.get("skill_id")
    if not isinstance(skill_id, str):
        return sorted(set(findings)), {}
    base_skill = _find_skill(base_registry, skill_id)
    candidate_skill = _find_skill(candidate_registry, skill_id)
    if base_skill is None or base_skill.get("lifecycle") != "development":
        findings.append(Finding("PROMOTION_BASE_LIFECYCLE_INVALID", skill_id, "base Skill must exist as development"))
    if candidate_skill is None or candidate_skill.get("lifecycle") != "active":
        findings.append(Finding("PROMOTION_CANDIDATE_LIFECYCLE_INVALID", skill_id, "candidate Skill must exist as active"))

    expected_source = f"skills/{skill_id}"
    transition = promotion.get("path_transition")
    if not isinstance(transition, dict) or transition.get("from") != expected_source or transition.get("to") != expected_source:
        findings.append(Finding("PROMOTION_PATH_TRANSITION_INVALID", "path_transition", f"both paths must equal {expected_source}"))
    try:
        tree_hash = repo.source_tree_sha256(candidate, expected_source)
    except GitError as exc:
        findings.append(Finding("PROMOTION_SOURCE_TREE_INVALID", expected_source, str(exc)))
        tree_hash = None
    if tree_hash is not None:
        declared_tree = transition.get("source_tree_sha256") if isinstance(transition, dict) else None
        registry_tree = candidate_skill.get("source_tree_sha256") if isinstance(candidate_skill, dict) else None
        if tree_hash != declared_tree or tree_hash != registry_tree:
            findings.append(Finding("PROMOTION_SOURCE_TREE_HASH_MISMATCH", expected_source, "candidate bytes, promotion delta, and Skill registry differ"))

    try:
        actual_diff = set(repo.diff_paths(base, candidate))
    except GitError as exc:
        findings.append(Finding("PROMOTION_DIFF_INVALID", "diff", str(exc)))
        actual_diff = set()
    declared_domain = promotion.get("domain_owned_files_changed")
    declared_shared = promotion.get("shared_files_changed")
    declared_diff = set(declared_domain if isinstance(declared_domain, list) else []) | set(declared_shared if isinstance(declared_shared, list) else [])
    if actual_diff != declared_diff:
        findings.append(
            Finding(
                "PROMOTION_DIFF_DECLARATION_MISMATCH",
                "changed_files",
                f"actual-only={sorted(actual_diff - declared_diff)} declared-only={sorted(declared_diff - actual_diff)}",
            )
        )
    if any(not str(path).startswith(f"{expected_source}/") for path in (declared_domain or [])):
        findings.append(Finding("PROMOTION_DOMAIN_PATH_OUTSIDE_SKILL", "domain_owned_files_changed", expected_source))

    findings.extend(_file_ref_findings(repo, candidate, promotion))

    referenced_paths: set[str] = set(actual_diff)
    for _path, node in _iter_dicts(promotion):
        candidate_path = _safe_path(node.get("path")) if isinstance(node, dict) else None
        if candidate_path:
            referenced_paths.add(candidate_path)
    record_index, index_findings = _build_record_index(repo, candidate, referenced_paths, selected_contracts)
    findings.extend(index_findings)

    activation_ref = promotion.get("activation_checklist")
    maturity_ref = promotion.get("task_maturity_catalog")
    activation: dict[str, Any] = {}
    maturity: dict[str, Any] = {}
    if isinstance(activation_ref, dict):
        try:
            _activation_file, activation = repo.json_file(candidate, activation_ref.get("path"))
            findings.extend(_schema_findings("activation-checklist@1.0", activation, selected_contracts, "activation_checklist"))
        except GitError as exc:
            findings.append(Finding("PROMOTION_ACTIVATION_RECORD_INVALID", "activation_checklist", str(exc)))
    if isinstance(maturity_ref, dict):
        try:
            _maturity_file, maturity = repo.json_file(candidate, maturity_ref.get("path"))
            findings.extend(_schema_findings("task-maturity@1.0", maturity, selected_contracts, "task_maturity_catalog"))
        except GitError as exc:
            findings.append(Finding("PROMOTION_MATURITY_RECORD_INVALID", "task_maturity_catalog", str(exc)))

    if activation:
        subject = activation.get("subject")
        if not isinstance(subject, dict) or subject.get("skill_id") != skill_id or subject.get("candidate_commit") != candidate:
            findings.append(Finding("PROMOTION_ACTIVATION_SUBJECT_MISMATCH", "activation_checklist/subject", "skill or candidate commit differs"))
        summary = activation.get("summary")
        expected_decision = promotion.get("decision")
        activation_decision = summary.get("decision") if isinstance(summary, dict) else None
        if activation_decision != expected_decision:
            findings.append(Finding("PROMOTION_DECISION_MISMATCH", "activation_checklist/summary", "activation and promotion decisions differ"))
        for path, node in _iter_dicts(activation):
            if set(node).issuperset({"path", "sha256"}) and isinstance(node.get("path"), str):
                if not node["path"].startswith(f"{expected_source}/"):
                    findings.append(Finding("PROMOTION_ACTIVATION_EVIDENCE_OUTSIDE_SKILL", _pointer(path), node["path"]))
        findings.extend(_file_ref_findings(repo, candidate, activation, prefix=("activation_checklist",)))
        findings.extend(_record_ref_findings(activation, record_index, prefix=("activation_checklist",)))
    if maturity:
        findings.extend(_file_ref_findings(repo, candidate, maturity, prefix=("task_maturity_catalog",)))
        findings.extend(_maturity_findings(maturity, skill_id, record_index))

    before_active = _active_set(base_registry)
    after_active = _active_set(candidate_registry)
    installer = promotion.get("installer_set")
    if isinstance(installer, dict):
        expected_installer = {
            "before": sorted(before_active),
            "after": sorted(after_active),
            "added": sorted(after_active - before_active),
            "removed": sorted(before_active - after_active),
        }
        for field, expected in expected_installer.items():
            actual = installer.get(field)
            if not isinstance(actual, list) or sorted(actual) != expected:
                findings.append(Finding("PROMOTION_INSTALLER_SET_MISMATCH", f"installer_set/{field}", f"expected {expected}"))
    if after_active - before_active != {skill_id}:
        findings.append(Finding("PROMOTION_ACTIVE_DELTA_INVALID", "installer_set", "exactly the promoted Skill must be added"))

    registry_paths = {
        "interface": "registry/interface-registry.yaml",
        "operation": "registry/operation-routes.yaml",
        "software": "registry/software-registry.yaml",
        "environment": "registry/environment-profiles.yaml",
    }
    candidate_registries: dict[str, dict[str, Any]] = {}
    for label, path in registry_paths.items():
        try:
            _item, value = repo.yaml_file(candidate, path)
            candidate_registries[label] = value
        except GitError as exc:
            findings.append(Finding("PROMOTION_SHARED_REGISTRY_INVALID", path, str(exc)))
    operation_routes = candidate_registries.get("operation", {}).get("routes")
    route = operation_routes.get(skill_id) if isinstance(operation_routes, dict) else None
    if not isinstance(route, dict) or route.get("lifecycle") != "active" or route.get("routable") is not True:
        findings.append(Finding("PROMOTION_OPERATION_ROUTE_INACTIVE", "registry/operation-routes.yaml", skill_id))

    interface_registry = candidate_registries.get("interface", {}).get("interfaces")
    for index_value, change in enumerate(promotion.get("interface_changes") or []):
        if not isinstance(change, dict) or change.get("action") not in {"activate", "add-active"}:
            continue
        interface_id = change.get("interface_id")
        entry = interface_registry.get(interface_id) if isinstance(interface_registry, dict) else None
        if not isinstance(entry, dict) or entry.get("lifecycle") != "active":
            findings.append(Finding("PROMOTION_INTERFACE_NOT_ACTIVE", f"interface_changes/{index_value}", str(interface_id)))

    software = candidate_registries.get("software", {})
    active_software = software.get("software") if isinstance(software, dict) else None
    planned_software = software.get("planned_software") if isinstance(software, dict) else None
    for index_value, move in enumerate(promotion.get("software_entries_moved") or []):
        software_id = move.get("software_id") if isinstance(move, dict) else None
        if not isinstance(active_software, dict) or software_id not in active_software:
            findings.append(Finding("PROMOTION_SOFTWARE_NOT_ACTIVE", f"software_entries_moved/{index_value}", str(software_id)))
        if isinstance(planned_software, dict) and software_id in planned_software:
            findings.append(Finding("PROMOTION_SOFTWARE_STILL_PLANNED", f"software_entries_moved/{index_value}", str(software_id)))

    status = "pass" if not findings else "fail"
    report = {
        "schema_version": "1.0",
        "validator": "commit-aware-promotion-validator",
        "promotion_id": promotion.get("promotion_id"),
        "skill_id": skill_id,
        "base_commit": base,
        "candidate_commit": candidate,
        "status": status,
        "eligible": status == "pass" and promotion.get("decision") == "eligible",
        "finding_count": len(set(findings)),
        "findings": [
            {"code": item.code, "location": item.location, "message": item.message}
            for item in sorted(set(findings))
        ],
    }
    return sorted(set(findings)), report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("promotion_delta", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contracts-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    findings, report = validate_promotion(
        args.root,
        args.promotion_delta,
        contracts_dir=args.contracts_dir,
    )
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 2
    if not report.get("eligible"):
        print("BLOCKED: promotion record is structurally and semantically valid but not eligible")
        return 3
    print("PASS: promotion is commit-bound, hash-closed, registry-consistent, and eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
