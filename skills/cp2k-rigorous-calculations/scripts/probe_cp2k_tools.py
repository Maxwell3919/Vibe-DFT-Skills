#!/usr/bin/env python3
"""Inventory CP2K executables and official Python tools without executing them."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
from typing import Any


TOOLS = {
    "cp2k-runtime": {
        "package": None,
        "source": "https://github.com/cp2k/cp2k",
        "commands": ["cp2k.psmp", "cp2k.popt", "cp2k.ssmp", "cp2k.sopt", "cp2k"],
    },
    "input-lint": {
        "package": "cp2k-input-tools",
        "source": "https://github.com/cp2k/cp2k-input-tools",
        "commands": ["cp2klint"],
    },
    "input-expand": {
        "package": "cp2k-input-tools",
        "source": "https://github.com/cp2k/cp2k-input-tools",
        "commands": ["fromcp2k"],
    },
    "restart-query": {
        "package": "cp2k-input-tools",
        "source": "https://github.com/cp2k/cp2k-input-tools",
        "commands": ["cp2kget"],
    },
    "output-parse": {
        "package": "cp2k-output-tools",
        "source": "https://github.com/cp2k/cp2k-output-tools",
        "commands": ["cp2kparse"],
    },
    "bands-convert": {
        "package": "cp2k-output-tools",
        "source": "https://github.com/cp2k/cp2k-output-tools",
        "commands": ["cp2k_bs2csv"],
    },
    "pdos-convolve": {
        "package": "cp2k-output-tools",
        "source": "https://github.com/cp2k/cp2k-output-tools",
        "commands": ["cp2k_pdos"],
    },
    "restart-trajectory-clean": {
        "package": "cp2k-output-tools",
        "source": "https://github.com/cp2k/cp2k-output-tools",
        "commands": ["xyz_restart_cleaner"],
    },
}


def package_version(name: str | None) -> str | None:
    if name is None:
        return None
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def probe() -> dict[str, Any]:
    capabilities: dict[str, dict[str, Any]] = {}
    for role, definition in TOOLS.items():
        detected = [command for command in definition["commands"] if shutil.which(command) is not None]
        capabilities[role] = {
            "available": bool(detected),
            "commands_detected": detected,
            "package": definition["package"],
            "package_version": package_version(definition["package"]),
            "official_source": definition["source"],
            "path_emitted": False,
            "execution_performed": False,
            "maturity_effect": "none",
        }
    return {
        "schema_version": "1.0",
        "probe": "probe_cp2k_tools.py",
        "capabilities": capabilities,
        "summary": {
            "available_roles": sum(record["available"] for record in capabilities.values()),
            "total_roles": len(capabilities),
        },
        "limitations": [
            "Availability does not establish version compatibility, adapter correctness, or scientific validity.",
            "No executable was invoked and no executable path was emitted.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    print(json.dumps(probe(), ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
