#!/usr/bin/env python3
"""Run all offline validation suites for the maintained DFT skills."""

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
        ([python, "tools/software_registry.py"], root),
        ([python, "tools/sync_contract_codes.py"], root),
        ([python, "tools/audit_repository.py"], root),
        ([python, "-m", "unittest", "discover", "-s", "tests", "-v"], root),
        ([python, "scripts/test_sync_official_manuals.py"], root / "skills" / "qe-rigorous-calculations"),
        ([python, "scripts/test_qe_guard.py"], root / "skills" / "qe-rigorous-calculations"),
        ([python, "scripts/sync_official_manuals.py", "--check"], root / "skills" / "qe-rigorous-calculations"),
        ([python, "scripts/test_skill_scripts.py"], root / "skills" / "vasp-rigorous-calculations"),
        ([python, "scripts/sync_official_wiki.py", "--check"], root / "skills" / "vasp-rigorous-calculations"),
        ([python, "scripts/test_skill_scripts.py"], root / "skills" / "cp2k-rigorous-calculations"),
        ([python, "scripts/sync_official_manuals.py", "--check"], root / "skills" / "cp2k-rigorous-calculations"),
        ([python, "scripts/sync_forward_fixtures.py", "--check"], root / "skills" / "cp2k-rigorous-calculations"),
        ([python, "scripts/test_skill_scripts.py"], root / "skills" / "siesta-rigorous-calculations"),
        ([python, "-m", "unittest", "discover", "-s", "tests", "-v"], root / "skills" / "cif-structure-analysis"),
        (
            [
                python,
                "-m",
                "compileall",
                "-q",
                "tools",
                "skills/dft-postprocess/scripts",
                "skills/dft-campaign-efficiency/scripts",
                "skills/cif-structure-analysis/scripts",
                "skills/cp2k-rigorous-calculations/scripts",
                "skills/qe-rigorous-calculations/scripts",
                "skills/siesta-rigorous-calculations/scripts",
                "skills/vasp-rigorous-calculations/scripts",
            ],
            root,
        ),
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
