#!/usr/bin/env python3
"""Run all offline validation suites for the four DFT skills."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def run(root: Path, command: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd or root, check=True)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    python = sys.executable
    commands = [
        ([python, "-m", "unittest", "discover", "-s", "tests", "-v"], root),
        ([python, "scripts/test_sync_official_manuals.py"], root / "skills" / "qe-rigorous-calculations"),
        ([python, "scripts/sync_official_manuals.py", "--check"], root / "skills" / "qe-rigorous-calculations"),
        ([python, "scripts/test_skill_scripts.py"], root / "skills" / "vasp-rigorous-calculations"),
        ([python, "scripts/sync_official_wiki.py", "--check"], root / "skills" / "vasp-rigorous-calculations"),
        ([python, "-m", "compileall", "-q", "tools", "skills/dft-postprocess/scripts", "skills/dft-campaign-efficiency/scripts", "skills/vasp-rigorous-calculations/scripts"], root),
    ]
    try:
        for command, cwd in commands:
            run(root, command, cwd)
    except subprocess.CalledProcessError as exc:
        return exc.returncode or 1
    print("PASS: all offline suites completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
