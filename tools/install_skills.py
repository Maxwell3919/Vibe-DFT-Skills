#!/usr/bin/env python3
"""Install repository skills into an explicit agent or tool skill directory."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from skill_registry import active_skill_names, validate_active_sources, validate_selected_active_sources


TARGET_ENV = "VIBE_DFT_SKILLS_TARGET"


def installable_skill_names(root: Path | None = None) -> tuple[str, ...]:
    selected_root = root or Path(__file__).resolve().parents[1]
    return validate_active_sources(selected_root)


def main() -> int:
    try:
        skills = active_skill_names()
    except (OSError, ValueError) as exc:
        print(f"invalid Skill registry: {exc}", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        help=f"destination skill directory (or set {TARGET_ENV})",
    )
    parser.add_argument("--skill", action="append", choices=skills)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    target_root = args.target
    if target_root is None:
        configured = os.environ.get(TARGET_ENV)
        if not configured:
            parser.error(f"--target is required unless {TARGET_ENV} is set")
        target_root = Path(configured).expanduser()
    selected = tuple(args.skill or skills)
    source_root = Path(__file__).resolve().parents[1] / "skills"
    failures = []
    actions: list[tuple[str, Path, Path, bool]] = []
    for name in selected:
        source = source_root / name
        target = target_root / name
        if not source.joinpath("SKILL.md").is_file():
            failures.append(f"missing source skill: {source}")
            continue
        if target.is_symlink() and target.resolve() == source.resolve():
            actions.append((f"already installed: {name}", source, target, False))
            continue
        if target.exists() or target.is_symlink():
            failures.append(f"refusing to replace existing path: {target}")
            continue
        actions.append((f"link {target} -> {source}", source, target, True))
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return 2
    try:
        validate_selected_active_sources(selected, Path(__file__).resolve().parents[1])
    except (OSError, ValueError) as exc:
        print(f"source validation failed: {exc}", file=sys.stderr)
        return 2
    for message, source, target, should_link in actions:
        print(message)
        if should_link and not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(source, target, target_is_directory=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
