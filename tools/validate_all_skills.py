#!/usr/bin/env python3
"""Validate all repository skills, UI metadata, links, and source boundaries."""

from __future__ import annotations

import re
from pathlib import Path
import sys

from registry_yaml import RegistryYAMLError, load_yaml_strict, loads_yaml_strict
from skill_registry import validate_source_skills


LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
MAX_SKILL_BYTES = 1024 * 1024


def validate_skill(path: Path) -> list[str]:
    failures: list[str] = []
    skill_file = path / "SKILL.md"
    if not skill_file.is_file():
        return [f"{path.name}: missing SKILL.md"]
    try:
        raw = skill_file.read_bytes()
        if len(raw) > MAX_SKILL_BYTES:
            return [f"{path.name}: SKILL.md exceeds the byte limit"]
        if raw.startswith(b"\xef\xbb\xbf"):
            return [f"{path.name}: SKILL.md UTF-8 BOM is forbidden"]
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return [f"{path.name}: SKILL.md is not strict UTF-8"]
    except OSError as exc:
        return [f"{path.name}: SKILL.md is unreadable ({exc.__class__.__name__})"]
    lines = text.splitlines()
    if len(lines) > 500:
        failures.append(f"{path.name}: SKILL.md exceeds 500 lines ({len(lines)})")
    if "TODO" in text:
        failures.append(f"{path.name}: unresolved TODO in SKILL.md")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        failures.append(f"{path.name}: invalid YAML frontmatter delimiters")
        return failures
    try:
        metadata = loads_yaml_strict(match.group(1), "SKILL.md-frontmatter")
    except RegistryYAMLError as exc:
        failures.append(f"{path.name}: invalid YAML frontmatter: {exc}")
        metadata = None
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
        try:
            agent = load_yaml_strict(agent_file, "openai.yaml")
        except RegistryYAMLError as exc:
            failures.append(f"{path.name}: invalid agents/openai.yaml: {exc}")
            agent = {}
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
        if clean:
            resolved = path.joinpath(clean).resolve()
            try:
                resolved.relative_to(path.resolve())
            except ValueError:
                failures.append(f"{path.name}: SKILL.md link escapes the Skill root")
            else:
                if not resolved.exists():
                    failures.append(f"{path.name}: broken SKILL.md link {target}")
    if path.joinpath("README.md").exists():
        failures.append(f"{path.name}: README.md is not allowed inside a skill")
    return failures


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    skills = sorted(path for path in (root / "skills").iterdir() if path.is_dir())
    try:
        expected = set(validate_source_skills(root))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
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
