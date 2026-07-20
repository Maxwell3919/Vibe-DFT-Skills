#!/usr/bin/env python3
"""Validate a two-phase development-to-active promotion against Git objects."""

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
ROUTING_REGISTRIES = (
    "registry/skill-registry.yaml",
    "registry/interface-registry.yaml",
    "registry/operation-routes.yaml",
    "registry/software-registry.yaml",
    "registry/environment-profiles.yaml",
)
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
    "format-fixture-validated": "input_gates_only",
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
        if self._run(["rev-parse", "--git-dir"]).returncode != 0:
            raise GitError("repository root is not a readable Git work tree")

    def _run(self, arguments: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def head(self) -> str:
        completed = self._run(["rev-parse", "HEAD^{commit}"])
        if completed.returncode != 0:
            raise GitError("HEAD does not resolve to a commit")
        return completed.stdout.decode("ascii", errors="strict").strip()

    def resolve_commit(self, value: object, label: str) -> str:
        if not isinstance(value, str) or len(value) not in (40, 64):
            raise GitError(f"{label}: commit must be an exact 40- or 64-character hex ID")
        completed = self._run(["rev-parse", "--verify", f"{value}^{{commit}}"])
        if completed.returncode != 0:
            raise GitError(f"{label}: commit does not resolve")
        resolved = completed.stdout.decode("ascii", errors="strict").strip()
        if resolved != value:
            raise GitError(f"{label}: commit must be canonical and exact")
        return resolved

    def is_ancestor(self, base: str, descendant: str) -> bool:
        return self._run(["merge-base", "--is-ancestor", base, descendant]).returncode == 0

    def file(self, commit: str, path_value: object) -> GitFile:
        path = _safe_path(path_value)
        if path is None:
            raise GitError(f"unsafe repository path: {path_value!r}")
        completed = self._run(["show", f"{commit}:{path}"])
        if completed.returncode != 0:
            raise GitError(f"{path}: file does not exist at {commit}")
        if len(completed.stdout) > MAX_GIT_FILE_BYTES:
            raise GitError(f"{path}: file exceeds the validation size limit")
        return GitFile(path=path, raw=completed.stdout)

    def json_file(self, commit: str, path_value: object) -> tuple[GitFile, dict[str, Any]]:
        item = self.file(commit, path_value)
        try:
            value = strict_json.loads_object(item.raw, item.path, max_bytes=MAX_GIT_FILE_BYTES)
        except strict_json.StrictJSONError as exc:
            raise GitError(f"{item.path}: strict JSON invalid: {exc}") from exc
        return item, value

    def yaml_file(self, commit: str, path_value: object) -> tuple[GitFile, dict[str, Any]]:
        item = self.file(commit, path_value)
        try:
            value = loads_yaml_strict(item.raw.decode("utf-8", errors="strict"), item.path)
        except (UnicodeDecodeError, RegistryYAMLError) as exc:
            raise GitError(f"{item.path}: strict YAML invalid: {exc}") from exc
        return item, value

    def diff_paths(self, base: str, descendant: str) -> tuple[str, ...]:
        completed = self._run(
            ["diff", "--name-only", "-z", "--diff-filter=ACMRT", base, descendant, "--"]
        )
        if completed.returncode != 0:
            raise GitError("commit diff cannot be enumerated")
        result = []
        for raw in completed.stdout.split(b"\0"):
            if not raw:
                continue
            path = _safe_path(raw.decode("utf-8", errors="strict"))
            if path is None:
                raise GitError("commit diff contains an unsafe path")
            result.append(path)
        return tuple(sorted(set(result)))

    def tree_paths(self, commit: str, prefix: str) -> tuple[str, ...]:
        safe_prefix = _safe_path(prefix)
        if safe_prefix is None:
            raise GitError("unsafe tree prefix")
        completed = self._run(
            ["ls-tree", "-r", "--name-only", "-z", commit, "--", safe_prefix]
        )
        if completed.returncode != 0:
            raise GitError(f"cannot enumerate source tree {safe_prefix}")
        return tuple(
            sorted(
                raw.decode("utf-8", errors="strict")
                for raw in completed.stdout.split(b"\0")
                if raw
            )
        )

    def source_tree_sha256(self, commit: str, prefix: str) -> str:
        prefix_path = PurePosixPath(prefix)
        files: list[tuple[str, bytes]] = []
        for full_path in self.tree_paths(commit, prefix):
            relative = PurePosixPath(full_path).relative_to(prefix_path).as_posix()
            relative_path = PurePosixPath(relative)
            if any(
                part in {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
                for part in relative_path.parts
            ):
                continue
            if relative_path.name in {".coverage", ".DS_Store"}:
                continue
            if relative_path.suffix.lower() in {".pyc", ".pyo", ".pyd"}:
                continue
            files.append((relative, self.file(commit, full_path).raw))
        if not files:
            raise GitError(f"{prefix}: source tree contains no Git blobs")
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


def _pointer(parts: Iterable[object]) -> str:
    values = tuple(parts)
    return "<root>" if not values else "/" + "/".join(str(value) for value in values)


def _iter_dicts(
    value: object,
    path: tuple[object, ...] = (),
) -> Iterator[tuple[tuple[object, ...], dict[str, Any]]]:
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from _iter_dicts(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_dicts(child, (*path, index))


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


def _skill_entry(registry: dict[str, Any], skill_id: str) -> dict[str, Any] | None:
    skills = registry.get("skills")
    value = skills.get(skill_id) if isinstance(skills, dict) else None
    return value if isinstance(value, dict) else None


def _verify_ref(
    repo: GitRepository,
    commit: str,
    reference: object,
    location: str,
    code_prefix: str,
) -> tuple[GitFile | None, list[Finding]]:
    if not isinstance(reference, dict):
        return None, [Finding(f"{code_prefix}_REF_INVALID", location, "reference must be an object")]
    try:
        item = repo.file(commit, reference.get("path"))
    except GitError as exc:
        return None, [Finding(f"{code_prefix}_REF_MISSING", location, str(exc))]
    if reference.get("sha256") != item.sha256:
        return item, [
            Finding(
                f"{code_prefix}_REF_HASH_MISMATCH",
                location,
                f"{item.path}: declared SHA-256 does not match Git bytes",
            )
        ]
    return item, []


def _candidate_refs(promotion: dict[str, Any]) -> Iterator[tuple[str, object]]:
    yield "task_maturity_catalog", promotion.get("task_maturity_catalog")
    for index, change in enumerate(promotion.get("interface_changes") or []):
        if isinstance(change, dict) and change.get("schema_ref") is not None:
            yield f"interface_changes/{index}/schema_ref", change.get("schema_ref")
    for index, change in enumerate(promotion.get("contracts_changed") or []):
        yield f"contracts_changed/{index}", change
    for index, decision in enumerate(promotion.get("observable_route_decisions") or []):
        if isinstance(decision, dict):
            yield f"observable_route_decisions/{index}/evidence", decision.get("evidence")


def _review_refs(promotion: dict[str, Any]) -> Iterator[tuple[str, object]]:
    yield "activation_checklist", promotion.get("activation_checklist")
    reports = promotion.get("reports")
    if isinstance(reports, dict):
        yield "reports/privacy_license", reports.get("privacy_license")
        for index, report in enumerate(reports.get("forward_tests") or []):
            yield f"reports/forward_tests/{index}", report


def _record_id(
    data: dict[str, Any],
    contract: validate_contract.ContractSchema,
) -> str | None:
    field = contract.record_id_field
    value = data.get(field) if field else None
    return value if isinstance(value, str) else None


def _record_index(
    repo: GitRepository,
    candidate: str,
    paths: Iterable[str],
    contracts_dir: Path,
) -> tuple[dict[tuple[str, str, str], tuple[str, str]], list[Finding]]:
    catalog = validate_contract.load_catalog(contracts_dir)
    index: dict[tuple[str, str, str], tuple[str, str]] = {}
    findings: list[Finding] = []
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
        resolved = (item.path, item.sha256)
        if key in index and index[key] != resolved:
            findings.append(
                Finding(
                    "PROMOTION_RECORD_ID_AMBIGUOUS",
                    item.path,
                    f"record identity {key!r} resolves to multiple candidate files",
                )
            )
        else:
            index[key] = resolved
    return index, findings


def _record_ref_findings(
    value: object,
    index: dict[tuple[str, str, str], tuple[str, str]],
    prefix: tuple[object, ...],
) -> list[Finding]:
    findings: list[Finding] = []
    for path, node in _iter_dicts(value, prefix):
        if not set(node).issuperset(
            {"contract_name", "schema_version", "record_id", "sha256"}
        ):
            continue
        key = (
            node.get("contract_name"),
            node.get("schema_version"),
            node.get("record_id"),
        )
        if not all(isinstance(item, str) for item in key):
            continue
        resolved = index.get(key)  # type: ignore[arg-type]
        if resolved is None:
            findings.append(
                Finding(
                    "PROMOTION_RECORD_REF_UNRESOLVED",
                    _pointer(path),
                    f"record reference {key!r} is absent from candidate evidence",
                )
            )
        elif resolved[1] != node.get("sha256"):
            findings.append(
                Finding(
                    "PROMOTION_RECORD_REF_HASH_MISMATCH",
                    _pointer(path),
                    f"record reference {key!r} does not match {resolved[0]}",
                )
            )
    return findings


def _activation_findings(
    repo: GitRepository,
    candidate: str,
    activation: dict[str, Any],
    skill_id: str,
    decision: object,
    record_index: dict[tuple[str, str, str], tuple[str, str]],
) -> list[Finding]:
    findings: list[Finding] = []
    subject = activation.get("subject")
    if (
        not isinstance(subject, dict)
        or subject.get("skill_id") != skill_id
        or subject.get("candidate_commit") != candidate
    ):
        findings.append(
            Finding(
                "PROMOTION_ACTIVATION_SUBJECT_MISMATCH",
                "activation_checklist/subject",
                "skill_id or candidate_commit differs from promotion",
            )
        )
    summary = activation.get("summary")
    if not isinstance(summary, dict) or summary.get("decision") != decision:
        findings.append(
            Finding(
                "PROMOTION_DECISION_MISMATCH",
                "activation_checklist/summary",
                "activation and promotion decisions differ",
            )
        )
    for path, node in _iter_dicts(activation, ("activation_checklist",)):
        if not set(node).issuperset({"path", "sha256"}):
            continue
        path_text = node.get("path")
        if not isinstance(path_text, str) or not path_text.startswith(f"skills/{skill_id}/"):
            findings.append(
                Finding(
                    "PROMOTION_ACTIVATION_EVIDENCE_OUTSIDE_SKILL",
                    _pointer(path),
                    str(path_text),
                )
            )
            continue
        _item, ref_findings = _verify_ref(
            repo,
            candidate,
            node,
            _pointer(path),
            "PROMOTION_CANDIDATE_EVIDENCE",
        )
        findings.extend(ref_findings)
    findings.extend(
        _record_ref_findings(activation, record_index, ("activation_checklist",))
    )
    return findings


def _maturity_findings(
    repo: GitRepository,
    candidate: str,
    maturity: dict[str, Any],
    skill_id: str,
    decision: object,
    record_index: dict[tuple[str, str, str], tuple[str, str]],
) -> list[Finding]:
    findings: list[Finding] = []
    if maturity.get("skill_id") != skill_id:
        findings.append(
            Finding(
                "PROMOTION_MATURITY_SKILL_MISMATCH",
                "task_maturity_catalog/skill_id",
                "skill_id differs from promotion",
            )
        )
    routes = maturity.get("routes")
    if not isinstance(routes, list):
        return findings
    route_map: dict[str, dict[str, Any]] = {}
    eligible_routes = 0
    for index, route in enumerate(routes):
        if not isinstance(route, dict) or not isinstance(route.get("route_id"), str):
            continue
        route_id = route["route_id"]
        if route_id in route_map:
            findings.append(
                Finding("PROMOTION_MATURITY_ROUTE_DUPLICATE", f"routes/{index}", route_id)
            )
        route_map[route_id] = route
        axes = [
            route.get("invocation_maturity"),
            route.get("parser_maturity"),
            route.get("scientific_validation_maturity"),
        ]
        if all(axis in MATURITY_ORDER for axis in axes):
            computed = min(axes, key=lambda item: MATURITY_ORDER[str(item)])
            overall = route.get("overall_maturity")
            if (
                not isinstance(overall, dict)
                or overall.get("declared") != computed
                or overall.get("computed") != computed
            ):
                findings.append(
                    Finding(
                        "PROMOTION_MATURITY_COMPUTED_MISMATCH",
                        f"routes/{index}/overall_maturity",
                        f"both values must equal {computed}",
                    )
                )
            ceiling = route.get("claim_ceiling")
            maximum = MATURITY_MAX_CLAIM[str(computed)]
            if ceiling in CLAIM_ORDER and CLAIM_ORDER[str(ceiling)] > CLAIM_ORDER[maximum]:
                findings.append(
                    Finding(
                        "PROMOTION_MATURITY_CLAIM_OVERSTATED",
                        f"routes/{index}/claim_ceiling",
                        f"{computed} caps claims at {maximum}",
                    )
                )
        if (
            route.get("provider_lifecycle") == "active"
            and route.get("implementation") == "implemented"
            and route.get("advertised") is True
            and route.get("overall_maturity", {}).get("computed")
            in {"real-artifact-validated", "tool-integration-validated"}
        ):
            eligible_routes += 1
        evidence_axes: set[str] = set()
        for evidence_index, evidence in enumerate(route.get("evidence") or []):
            if not isinstance(evidence, dict):
                continue
            axis = evidence.get("axis")
            if isinstance(axis, str):
                evidence_axes.add(axis)
            if evidence.get("source") == "skill-local":
                path_text = evidence.get("path")
                if not isinstance(path_text, str) or not path_text.startswith(
                    f"skills/{skill_id}/"
                ):
                    findings.append(
                        Finding(
                            "PROMOTION_MATURITY_EVIDENCE_OUTSIDE_SKILL",
                            f"routes/{index}/evidence/{evidence_index}",
                            str(path_text),
                        )
                    )
                else:
                    _item, ref_findings = _verify_ref(
                        repo,
                        candidate,
                        evidence,
                        f"routes/{index}/evidence/{evidence_index}",
                        "PROMOTION_CANDIDATE_EVIDENCE",
                    )
                    findings.extend(ref_findings)
        for field, axis in (
            ("invocation_maturity", "invocation"),
            ("parser_maturity", "parser"),
            ("scientific_validation_maturity", "scientific_validation"),
        ):
            if route.get(field) != "design-only" and axis not in evidence_axes:
                findings.append(
                    Finding(
                        "PROMOTION_MATURITY_AXIS_EVIDENCE_MISSING",
                        f"routes/{index}/{field}",
                        f"no {axis} evidence is declared",
                    )
                )
    if decision == "eligible" and eligible_routes == 0:
        findings.append(
            Finding(
                "PROMOTION_NO_ELIGIBLE_ROUTE",
                "task_maturity_catalog/routes",
                "eligible promotion requires an advertised implemented route with real-artifact or tool-integration maturity",
            )
        )

    graph: dict[str, str | None] = {}
    for route_id, route in route_map.items():
        parent = route.get("parent_route")
        if isinstance(parent, dict) and parent.get("scope") == "catalog":
            parent_id = parent.get("route_id")
            if not isinstance(parent_id, str) or parent_id not in route_map:
                findings.append(
                    Finding("PROMOTION_MATURITY_PARENT_MISSING", route_id, str(parent_id))
                )
                graph[route_id] = None
            else:
                graph[route_id] = parent_id
        else:
            graph[route_id] = None
    for start in graph:
        visited: set[str] = set()
        current: str | None = start
        while current is not None:
            if current in visited:
                findings.append(
                    Finding("PROMOTION_MATURITY_PARENT_CYCLE", start, current)
                )
                break
            visited.add(current)
            current = graph.get(current)
    findings.extend(
        _record_ref_findings(maturity, record_index, ("task_maturity_catalog",))
    )
    return findings


def _registry_cross_findings(
    repo: GitRepository,
    candidate: str,
    review: str,
    promotion: dict[str, Any],
    candidate_skill_registry: dict[str, Any],
) -> list[Finding]:
    findings: list[Finding] = []
    skill_id = promotion.get("skill_id")
    candidate_registries: dict[str, dict[str, Any]] = {}
    for path in ROUTING_REGISTRIES:
        try:
            candidate_file, candidate_value = repo.yaml_file(candidate, path)
            review_file = repo.file(review, path)
            candidate_registries[path] = candidate_value
            if review_file.raw != candidate_file.raw:
                findings.append(
                    Finding(
                        "PROMOTION_REVIEW_REGISTRY_CHANGED",
                        path,
                        "review commit must not change candidate routing registries",
                    )
                )
        except GitError as exc:
            findings.append(Finding("PROMOTION_SHARED_REGISTRY_INVALID", path, str(exc)))

    operation = candidate_registries.get("registry/operation-routes.yaml", {})
    routes = operation.get("routes") if isinstance(operation, dict) else None
    route = routes.get(skill_id) if isinstance(routes, dict) else None
    if (
        not isinstance(route, dict)
        or route.get("lifecycle") != "active"
        or route.get("routable") is not True
    ):
        findings.append(
            Finding(
                "PROMOTION_OPERATION_ROUTE_INACTIVE",
                "registry/operation-routes.yaml",
                str(skill_id),
            )
        )

    interfaces = candidate_registries.get("registry/interface-registry.yaml", {}).get(
        "interfaces"
    )
    for index, change in enumerate(promotion.get("interface_changes") or []):
        if not isinstance(change, dict) or change.get("action") not in {
            "activate",
            "add-active",
        }:
            continue
        interface_id = change.get("interface_id")
        entry = interfaces.get(interface_id) if isinstance(interfaces, dict) else None
        if not isinstance(entry, dict) or entry.get("lifecycle") != "active":
            findings.append(
                Finding(
                    "PROMOTION_INTERFACE_NOT_ACTIVE",
                    f"interface_changes/{index}",
                    str(interface_id),
                )
            )

    software_registry = candidate_registries.get("registry/software-registry.yaml", {})
    active_software = software_registry.get("software")
    planned_software = software_registry.get("planned_software")
    for index, move in enumerate(promotion.get("software_entries_moved") or []):
        software_id = move.get("software_id") if isinstance(move, dict) else None
        if not isinstance(active_software, dict) or software_id not in active_software:
            findings.append(
                Finding(
                    "PROMOTION_SOFTWARE_NOT_ACTIVE",
                    f"software_entries_moved/{index}",
                    str(software_id),
                )
            )
        if isinstance(planned_software, dict) and software_id in planned_software:
            findings.append(
                Finding(
                    "PROMOTION_SOFTWARE_STILL_PLANNED",
                    f"software_entries_moved/{index}",
                    str(software_id),
                )
            )

    before = _active_set(candidate_skill_registry)
    if skill_id not in before:
        findings.append(
            Finding(
                "PROMOTION_CANDIDATE_ACTIVE_SET_INVALID",
                "registry/skill-registry.yaml",
                "promoted Skill is absent from candidate active set",
            )
        )
    return findings


def validate_promotion(
    root: Path,
    promotion_path: Path,
    *,
    review_commit: str | None = None,
    contracts_dir: Path | None = None,
) -> tuple[list[Finding], dict[str, Any]]:
    root = root.resolve()
    contracts = (contracts_dir or root / "contracts").resolve()
    findings: list[Finding] = []
    try:
        raw = promotion_path.read_bytes()
        promotion = strict_json.loads_object(
            raw, promotion_path.name, max_bytes=MAX_GIT_FILE_BYTES
        )
    except (OSError, strict_json.StrictJSONError) as exc:
        return [Finding("PROMOTION_INPUT_INVALID", str(promotion_path), str(exc))], {}
    findings.extend(
        _schema_findings("promotion-delta@1.1", promotion, contracts, "promotion")
    )

    try:
        repo = GitRepository(root)
        base = repo.resolve_commit(promotion.get("base_commit"), "base_commit")
        candidate = repo.resolve_commit(
            promotion.get("candidate_commit"), "candidate_commit"
        )
        review = (
            repo.resolve_commit(review_commit, "review_commit")
            if review_commit is not None
            else repo.head()
        )
    except GitError as exc:
        return sorted(
            set(findings + [Finding("PROMOTION_COMMIT_INVALID", "commits", str(exc))])
        ), {}
    if base == candidate or not repo.is_ancestor(base, candidate):
        findings.append(
            Finding(
                "PROMOTION_CANDIDATE_ORDER_INVALID",
                "commits",
                "base must be a strict ancestor of candidate",
            )
        )
    if candidate == review or not repo.is_ancestor(candidate, review):
        findings.append(
            Finding(
                "PROMOTION_REVIEW_ORDER_INVALID",
                "commits",
                "candidate must be a strict ancestor of review",
            )
        )

    skill_id = promotion.get("skill_id")
    if not isinstance(skill_id, str):
        return sorted(set(findings)), {}
    source_root = f"skills/{skill_id}"
    expected_review_root = f"evidence/promotions/{skill_id}"
    if promotion.get("review_artifact_root") != expected_review_root:
        findings.append(
            Finding(
                "PROMOTION_REVIEW_ROOT_INVALID",
                "review_artifact_root",
                f"expected {expected_review_root}",
            )
        )

    try:
        local_relative = promotion_path.resolve().relative_to(root).as_posix()
    except ValueError:
        findings.append(
            Finding(
                "PROMOTION_RECORD_OUTSIDE_REPOSITORY",
                str(promotion_path),
                "promotion record must be committed under the review artifact root",
            )
        )
        local_relative = ""
    if local_relative and not local_relative.startswith(f"{expected_review_root}/"):
        findings.append(
            Finding(
                "PROMOTION_RECORD_OUTSIDE_REVIEW_ROOT",
                local_relative,
                expected_review_root,
            )
        )
    if local_relative:
        try:
            committed_promotion = repo.file(review, local_relative)
            if committed_promotion.raw != raw:
                findings.append(
                    Finding(
                        "PROMOTION_RECORD_BYTES_MISMATCH",
                        local_relative,
                        "local bytes differ from review commit",
                    )
                )
        except GitError as exc:
            findings.append(
                Finding("PROMOTION_RECORD_NOT_COMMITTED", local_relative, str(exc))
            )

    try:
        base_registry_file, base_registry = repo.yaml_file(
            base, "registry/skill-registry.yaml"
        )
        _candidate_registry_file, candidate_registry = repo.yaml_file(
            candidate, "registry/skill-registry.yaml"
        )
    except GitError as exc:
        findings.append(
            Finding(
                "PROMOTION_SKILL_REGISTRY_INVALID",
                "registry/skill-registry.yaml",
                str(exc),
            )
        )
        return sorted(set(findings)), {}
    if promotion.get("base_registry_sha256") != base_registry_file.sha256:
        findings.append(
            Finding(
                "PROMOTION_BASE_REGISTRY_HASH_MISMATCH",
                "base_registry_sha256",
                "does not match base commit bytes",
            )
        )

    base_skill = _skill_entry(base_registry, skill_id)
    candidate_skill = _skill_entry(candidate_registry, skill_id)
    if base_skill is None or base_skill.get("lifecycle") != "development":
        findings.append(
            Finding(
                "PROMOTION_BASE_LIFECYCLE_INVALID",
                skill_id,
                "base Skill must be development",
            )
        )
    if candidate_skill is None or candidate_skill.get("lifecycle") != "active":
        findings.append(
            Finding(
                "PROMOTION_CANDIDATE_LIFECYCLE_INVALID",
                skill_id,
                "candidate Skill must be active",
            )
        )

    transition = promotion.get("path_transition")
    if (
        not isinstance(transition, dict)
        or transition.get("from") != source_root
        or transition.get("to") != source_root
    ):
        findings.append(
            Finding(
                "PROMOTION_PATH_TRANSITION_INVALID",
                "path_transition",
                f"from and to must equal {source_root}",
            )
        )
    try:
        tree_hash = repo.source_tree_sha256(candidate, source_root)
    except GitError as exc:
        findings.append(
            Finding("PROMOTION_SOURCE_TREE_INVALID", source_root, str(exc))
        )
        tree_hash = None
    if tree_hash is not None:
        delta_hash = transition.get("source_tree_sha256") if isinstance(transition, dict) else None
        registry_hash = (
            candidate_skill.get("source_tree_sha256")
            if isinstance(candidate_skill, dict)
            else None
        )
        if tree_hash != delta_hash or tree_hash != registry_hash:
            findings.append(
                Finding(
                    "PROMOTION_SOURCE_TREE_HASH_MISMATCH",
                    source_root,
                    "candidate bytes, promotion delta, and Skill registry differ",
                )
            )

    try:
        candidate_diff = set(repo.diff_paths(base, candidate))
        review_diff = set(repo.diff_paths(candidate, review))
    except GitError as exc:
        findings.append(Finding("PROMOTION_DIFF_INVALID", "diff", str(exc)))
        candidate_diff = set()
        review_diff = set()
    declared_domain = promotion.get("domain_owned_files_changed")
    declared_shared = promotion.get("shared_files_changed")
    declared_candidate_diff = set(
        declared_domain if isinstance(declared_domain, list) else []
    ) | set(declared_shared if isinstance(declared_shared, list) else [])
    if candidate_diff != declared_candidate_diff:
        findings.append(
            Finding(
                "PROMOTION_CANDIDATE_DIFF_MISMATCH",
                "changed_files",
                f"actual-only={sorted(candidate_diff - declared_candidate_diff)} "
                f"declared-only={sorted(declared_candidate_diff - candidate_diff)}",
            )
        )
    if any(
        not isinstance(path, str) or not path.startswith(f"{source_root}/")
        for path in (declared_domain or [])
    ):
        findings.append(
            Finding(
                "PROMOTION_DOMAIN_PATH_OUTSIDE_SKILL",
                "domain_owned_files_changed",
                source_root,
            )
        )
    illegal_review_paths = sorted(
        path for path in review_diff if not path.startswith(f"{expected_review_root}/")
    )
    if illegal_review_paths:
        findings.append(
            Finding(
                "PROMOTION_REVIEW_DIFF_ESCAPES_ARTIFACT_ROOT",
                "review_diff",
                str(illegal_review_paths),
            )
        )

    candidate_ref_paths: set[str] = set(candidate_diff)
    for location, reference in _candidate_refs(promotion):
        item, ref_findings = _verify_ref(
            repo, candidate, reference, location, "PROMOTION_CANDIDATE"
        )
        findings.extend(ref_findings)
        if item is not None:
            candidate_ref_paths.add(item.path)
    for location, reference in _review_refs(promotion):
        item, ref_findings = _verify_ref(
            repo, review, reference, location, "PROMOTION_REVIEW"
        )
        findings.extend(ref_findings)
        if item is not None and not item.path.startswith(f"{expected_review_root}/"):
            findings.append(
                Finding(
                    "PROMOTION_REVIEW_REF_OUTSIDE_ROOT",
                    location,
                    item.path,
                )
            )

    record_index, index_findings = _record_index(
        repo, candidate, candidate_ref_paths, contracts
    )
    findings.extend(index_findings)

    activation: dict[str, Any] = {}
    maturity: dict[str, Any] = {}
    activation_ref = promotion.get("activation_checklist")
    maturity_ref = promotion.get("task_maturity_catalog")
    if isinstance(activation_ref, dict):
        try:
            _item, activation = repo.json_file(review, activation_ref.get("path"))
            findings.extend(
                _schema_findings(
                    "activation-checklist@1.1",
                    activation,
                    contracts,
                    "activation_checklist",
                )
            )
        except GitError as exc:
            findings.append(
                Finding(
                    "PROMOTION_ACTIVATION_RECORD_INVALID",
                    "activation_checklist",
                    str(exc),
                )
            )
    if isinstance(maturity_ref, dict):
        try:
            _item, maturity = repo.json_file(candidate, maturity_ref.get("path"))
            findings.extend(
                _schema_findings(
                    "task-maturity@1.1",
                    maturity,
                    contracts,
                    "task_maturity_catalog",
                )
            )
        except GitError as exc:
            findings.append(
                Finding(
                    "PROMOTION_MATURITY_RECORD_INVALID",
                    "task_maturity_catalog",
                    str(exc),
                )
            )
    if activation:
        findings.extend(
            _activation_findings(
                repo,
                candidate,
                activation,
                skill_id,
                promotion.get("decision"),
                record_index,
            )
        )
    if maturity:
        findings.extend(
            _maturity_findings(
                repo,
                candidate,
                maturity,
                skill_id,
                promotion.get("decision"),
                record_index,
            )
        )

    before_active = _active_set(base_registry)
    after_active = _active_set(candidate_registry)
    installer = promotion.get("installer_set")
    expected_installer = {
        "before": sorted(before_active),
        "after": sorted(after_active),
        "added": sorted(after_active - before_active),
        "removed": sorted(before_active - after_active),
    }
    if isinstance(installer, dict):
        for field, expected in expected_installer.items():
            actual = installer.get(field)
            if not isinstance(actual, list) or sorted(actual) != expected:
                findings.append(
                    Finding(
                        "PROMOTION_INSTALLER_SET_MISMATCH",
                        f"installer_set/{field}",
                        f"expected {expected}",
                    )
                )
    if after_active - before_active != {skill_id} or before_active - after_active:
        findings.append(
            Finding(
                "PROMOTION_ACTIVE_DELTA_INVALID",
                "installer_set",
                "exactly the promoted Skill must be added and none removed",
            )
        )

    findings.extend(
        _registry_cross_findings(
            repo, candidate, review, promotion, candidate_registry
        )
    )

    findings = sorted(set(findings))
    status = "pass" if not findings else "fail"
    report = {
        "schema_version": "1.0",
        "validator": "two-phase-promotion-validator",
        "promotion_id": promotion.get("promotion_id"),
        "skill_id": skill_id,
        "base_commit": base,
        "candidate_commit": candidate,
        "review_commit": review,
        "status": status,
        "eligible": status == "pass" and promotion.get("decision") == "eligible",
        "finding_count": len(findings),
        "findings": [
            {"code": item.code, "location": item.location, "message": item.message}
            for item in findings
        ],
    }
    return findings, report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("promotion_delta", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--review-commit")
    parser.add_argument("--contracts-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    findings, report = validate_promotion(
        args.root,
        args.promotion_delta,
        review_commit=args.review_commit,
        contracts_dir=args.contracts_dir,
    )
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 2
    if not report.get("eligible"):
        print("BLOCKED: promotion evidence is valid but decision is blocked")
        return 3
    print(
        "PASS: two-phase promotion is commit-bound, hash-closed, "
        "registry-consistent, and eligible"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
