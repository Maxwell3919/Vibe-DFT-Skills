#!/usr/bin/env python3
"""Install repository skills as symlinks without overwriting real directories."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


SKILLS = (
    "qe-rigorous-calculations",
    "vasp-rigorous-calculations",
    "dft-postprocess",
    "dft-campaign-efficiency",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=Path.home() / ".codex" / "skills")
    parser.add_argument("--skill", action="append", choices=SKILLS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    selected = tuple(args.skill or SKILLS)
    source_root = Path(__file__).resolve().parents[1] / "skills"
    failures = []
    actions = []
    for name in selected:
        source = source_root / name
        target = args.target / name
        if not source.joinpath("SKILL.md").is_file():
            failures.append(f"missing source skill: {source}")
            continue
        if target.is_symlink() and target.resolve() == source.resolve():
            actions.append(f"already installed: {name}")
            continue
        if target.exists() or target.is_symlink():
            failures.append(f"refusing to replace existing path: {target}")
            continue
        actions.append(f"link {target} -> {source}")
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(source, target, target_is_directory=True)
    for item in actions:
        print(item)
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
