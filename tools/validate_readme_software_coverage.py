#!/usr/bin/env python3
"""Validate README software coverage, acknowledgements, and prose constraints."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import Any

from registry_yaml import load_yaml_strict


SOFTWARE_TABLE_HEADER = (
    "| 软件 | 数值方法或科学角色 | 代表性任务 | 当前涉及范围 |"
)
FORBIDDEN_SOFTWARE_COLUMNS = {
    "Lifecycle",
    "lifecycle",
    "Maturity",
    "maturity",
    "Support status",
    "支持状态",
    "局限",
    "Why included",
}
TEMPLATED_PROSE = (
    re.compile(r"不是[^。\n]{0,80}而是"),
    re.compile(r"并非[^。\n]{0,80}而是"),
    re.compile(r"不只是"),
    re.compile(r"不仅[^。\n]{0,80}更"),
    re.compile(r"赋能"),
    re.compile(r"端到端闭环"),
    re.compile(r"智能化生态"),
    re.compile(r"革命性"),
)
EXPECTED_SHOWCASE = {
    "docs/images/dft-evidence-workflow.png",
    "docs/images/software-landscape.png",
    "docs/images/synthetic-bands-dos.png",
    "docs/images/synthetic-convergence.png",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _section(text: str, start: str, end: str) -> str:
    try:
        start_index = text.index(start)
        end_index = text.index(end, start_index + len(start))
    except ValueError as exc:
        raise ValueError(f"README section boundary is missing: {start!r} -> {end!r}") from exc
    return text[start_index:end_index]


def _requirement_names(path: Path) -> tuple[str, ...]:
    names: list[str] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if match is None:
            raise ValueError(
                f"{path.name}:{line_number}: cannot identify requirement distribution"
            )
        names.append(match.group(1))
    if len(names) != len(set(names)):
        raise ValueError(f"{path.name}: duplicate requirement distributions")
    return tuple(names)


def validation_errors(
    root: Path,
    *,
    readme_path: Path | None = None,
    registry_path: Path | None = None,
    requirements_path: Path | None = None,
) -> list[str]:
    readme = readme_path or root / "README.md"
    registry = registry_path or root / "registry" / "software-registry.yaml"
    requirements = requirements_path or root / "requirements-dev.txt"
    failures: list[str] = []

    try:
        text = readme.read_text(encoding="utf-8")
        acknowledgements = _section(
            text,
            "> <details>",
            "> </details>",
        )
        landscape = _section(
            text,
            "## 科学软件版图",
            "## Skills 如何接力",
        )
        software_data = load_yaml_strict(registry, registry.name)
        requirement_names = _requirement_names(requirements)
    except (OSError, ValueError) as exc:
        return [str(exc)]

    active = software_data.get("software")
    planned = software_data.get("planned_software")
    if not isinstance(active, dict) or not isinstance(planned, dict):
        return [f"{registry.name}: expected software and planned_software mappings"]
    software: dict[str, Any] = {**active, **planned}

    expected_rows = len(software)
    observed_rows = 0
    for line in landscape.splitlines():
        if re.match(r"^\| `[a-z0-9-]+` · ", line):
            observed_rows += 1
    if observed_rows != expected_rows:
        failures.append(
            f"software landscape has {observed_rows} identity rows, expected {expected_rows}"
        )

    for software_id, metadata in software.items():
        row_token = f"| `{software_id}` · "
        row_count = landscape.count(row_token)
        if row_count != 1:
            failures.append(
                f"software {software_id!r} appears in {row_count} landscape rows, expected 1"
            )
        acknowledgement_token = f"(`{software_id}`)"
        acknowledgement_count = acknowledgements.count(acknowledgement_token)
        if acknowledgement_count != 1:
            failures.append(
                f"software {software_id!r} appears {acknowledgement_count} times "
                "in acknowledgements, expected 1"
            )
        display_name = metadata.get("display_name")
        if not isinstance(display_name, str) or display_name not in landscape:
            failures.append(
                f"software {software_id!r} display name is absent from the landscape"
            )

    header_count = landscape.count(SOFTWARE_TABLE_HEADER)
    if header_count < 1:
        failures.append("software landscape does not use the canonical four-column header")
    for line in landscape.splitlines():
        if not line.startswith("| 软件 |"):
            continue
        if line != SOFTWARE_TABLE_HEADER:
            failures.append(f"non-canonical software table header: {line}")
    for column in FORBIDDEN_SOFTWARE_COLUMNS:
        if f"| {column} |" in landscape:
            failures.append(
                f"software landscape contains a second status/coverage column: {column!r}"
            )

    for distribution in requirement_names:
        token = f"(`{distribution}`)"
        count = acknowledgements.count(token)
        if count != 1:
            failures.append(
                f"requirement {distribution!r} appears {count} times in acknowledgements, expected 1"
            )
    if acknowledgements.count(
        "https://github.com/helloworld-Co/html2md"
    ) != 1:
        failures.append(
            "helloworld-Co/html2md must appear exactly once in acknowledgements"
        )

    for pattern in TEMPLATED_PROSE:
        for match in pattern.finditer(text):
            line_number = text.count("\n", 0, match.start()) + 1
            failures.append(
                f"README.md:{line_number}: templated prose matches {pattern.pattern!r}"
            )

    for relative in EXPECTED_SHOWCASE:
        if relative not in text:
            failures.append(f"README does not reference showcase image {relative!r}")
        image = root / relative
        if not image.is_file() or image.stat().st_size == 0:
            failures.append(f"showcase image is absent or empty: {relative!r}")

    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument("--readme", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--requirements", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.resolve()
    failures = validation_errors(
        root,
        readme_path=args.readme,
        registry_path=args.registry,
        requirements_path=args.requirements,
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    software = load_yaml_strict(
        args.registry or root / "registry" / "software-registry.yaml",
        "software-registry.yaml",
    )
    requirement_names = _requirement_names(
        args.requirements or root / "requirements-dev.txt"
    )
    software_count = len(software["software"]) + len(software["planned_software"])
    print(
        "PASS: README covers "
        f"{software_count} registered software identities, "
        f"{len(requirement_names)} direct requirements, "
        "html2md, canonical scope columns, and prose constraints"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
