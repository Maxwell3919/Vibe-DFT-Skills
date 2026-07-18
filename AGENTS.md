# AGENTS.md — Vibe DFT Skills

## Scope

This private repository is the single source of truth for portable, maintainable DFT calculation, postprocessing, campaign-efficiency, and structure-analysis skills.

## Boundaries

- Keep every calculation code's official documentation separate from project experience and current analysis.
- Never commit licensed or restricted potential contents such as POTCAR, credentials, private hosts/accounts, raw calculation trees, unpublished numerical results, or real local/server paths.
- Use anonymized identifiers in tests and examples.
- Treat calculation correctness, execution completion, numerical convergence, physical validity, postprocessing validity, and efficiency as separate gates.
- Never improve efficiency by weakening a scientific acceptance criterion.
- Keep runtime experience databases outside Git; version schemas, migrations, rules, and synthetic fixtures only.

## Skill maintenance

- Edit the source under `skills/`; installed skills should be symlinks to this repository after migration.
- Keep the core `SKILL.md`, references, contracts, and deterministic CLIs independent of any single agent or tool vendor. Vendor-specific metadata such as `agents/openai.yaml` is an optional integration layer.
- Permit external tools through explicit adapters and registry entries; require version, provenance, input/output contracts, failure semantics, and maturity evidence instead of relying on a vendor allowlist.
- Keep every `SKILL.md` concise, imperative, and below 500 lines.
- Put detailed contracts and workflows in one-level `references/` files.
- Put deterministic behavior in tested scripts rather than prose.
- Do not add README files inside individual skill directories.
- Preserve official mirror provenance and refresh transactionally.
- Register calculation codes, calculation Skill locations, capability catalogs, and service interfaces in `registry/software-registry.yaml`; do not add an independent software list.
- Register every postprocessing observable/code/backend route in `skills/dft-postprocess/references/observable-registry.yaml`, including explicit `design-only` routes.

## Validation

Before commit or push, run:

```text
python3 tools/run_tests.py
python3 tools/validate_all_skills.py
python3 tools/audit_repository.py
git diff --check -- . ':(exclude)skills/qe-rigorous-calculations/references/official-*'
```

The QE `official-*` mirror preserves generated official text and is verified by its manifest-aware `--check`; do not rewrite it merely to satisfy generic whitespace rules.

Inspect `git status`, scan for sensitive paths/identifiers, and confirm no runtime database or calculation output is staged.
