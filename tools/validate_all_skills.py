#!/usr/bin/env python3
"""Validate all repository skills, UI metadata, links, and source boundaries."""

from __future__ import annotations

import re
from pathlib import Path
import sys

import yaml


LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def validate_skill(path: Path) -> list[str]:
    failures: list[str] = []
    skill_file = path / "SKILL.md"
    if not skill_file.is_file():
        return [f"{path.name}: missing SKILL.md"]
    text = skill_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) > 500:
        failures.append(f"{path.name}: SKILL.md exceeds 500 lines ({len(lines)})")
    if "TODO" in text:
        failures.append(f"{path.name}: unresolved TODO in SKILL.md")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        failures.append(f"{path.name}: invalid YAML frontmatter delimiters")
        return failures
    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict) or set(metadata) != {"name", "description"}:
        failures.append(f"{path.name}: frontmatter must contain only name and description")
    elif metadata["name"] != path.name:
        failures.append(f"{path.name}: frontmatter name mismatch")
    elif not isinstance(metadata["description"], str) or len(metadata["description"]) < 80:
        failures.append(f"{path.name}: description is too short for reliable triggering")
    agent_file = path / "agents" / "openai.yaml"
    if not agent_file.is_file():
        failures.append(f"{path.name}: missing agents/openai.yaml")
    else:
        agent = yaml.safe_load(agent_file.read_text(encoding="utf-8"))
        interface = agent.get("interface", {}) if isinstance(agent, dict) else {}
        short = interface.get("short_description", "")
        prompt = interface.get("default_prompt", "")
        if not 25 <= len(short) <= 64:
            failures.append(f"{path.name}: short_description length is {len(short)}, expected 25-64")
        if f"${path.name}" not in prompt:
            failures.append(f"{path.name}: default_prompt does not mention ${path.name}")
    for target in LINK.findall(text):
        if target.startswith(("http://", "https://", "#")):
            continue
        clean = target.split("#", 1)[0]
        if clean and not path.joinpath(clean).resolve().exists():
            failures.append(f"{path.name}: broken SKILL.md link {target}")
    if path.joinpath("README.md").exists():
        failures.append(f"{path.name}: README.md is not allowed inside a skill")
    return failures


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    skills = sorted(path for path in (root / "skills").iterdir() if path.is_dir())
    expected = {
        "qe-rigorous-calculations",
        "vasp-rigorous-calculations",
        "dft-postprocess",
        "dft-campaign-efficiency",
    }
    failures = []
    if {path.name for path in skills} != expected:
        failures.append(f"skill set mismatch: {sorted(path.name for path in skills)}")
    for path in skills:
        failures.extend(validate_skill(path))
    if (root / "skills" / "qe-rigorous-calculations" / "experience").exists():
        failures.append("QE skill must not contain project experience")
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return 2
    print(f"PASS: validated {len(skills)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
