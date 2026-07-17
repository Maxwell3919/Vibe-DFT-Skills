# AGENTS.md — DFT Codex Skills

## Scope

This private repository is the single source of truth for four DFT skills: rigorous QE calculations, rigorous VASP calculations, deterministic postprocessing, and evidence-backed campaign efficiency.

## Boundaries

- Keep official QE/VASP documentation separate from project experience and current analysis.
- Never commit POTCAR contents, credentials, private hosts/accounts, raw calculation trees, unpublished numerical results, or real local/server paths.
- Use anonymized identifiers in tests and examples.
- Treat calculation correctness, execution completion, numerical convergence, physical validity, postprocessing validity, and efficiency as separate gates.
- Never improve efficiency by weakening a scientific acceptance criterion.
- Keep runtime experience databases outside Git; version schemas, migrations, rules, and synthetic fixtures only.

## Skill maintenance

- Edit the source under `skills/`; installed skills must be symlinks to this repository after migration.
- Keep every `SKILL.md` concise, imperative, and below 500 lines.
- Put detailed contracts and workflows in one-level `references/` files.
- Put deterministic behavior in tested scripts rather than prose.
- Do not add README files inside individual skill directories.
- Preserve official mirror provenance and refresh transactionally.

## Validation

Before commit or push, run:

```text
python3 tools/run_tests.py
python3 tools/validate_all_skills.py
git diff --check -- . ':(exclude)skills/qe-rigorous-calculations/references/official-*'
```

The QE `official-*` mirror preserves generated official text and is verified by its manifest-aware `--check`; do not rewrite it merely to satisfy generic whitespace rules.

Inspect `git status`, scan for sensitive paths/identifiers, and confirm no runtime database or calculation output is staged.
