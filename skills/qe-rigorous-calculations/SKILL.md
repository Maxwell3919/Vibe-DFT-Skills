---
name: qe-rigorous-calculations
description: Design, explain, audit, troubleshoot, and validate rigorous Quantum ESPRESSO calculations using official documentation discovered under quantum-espresso.org/Doc/ and observable-specific numerical evidence. Use for QE input parameters, defaults, units, prerequisites, pw.x/ph.x/neb.x/postprocessing workflows, convergence studies, relax/static/bands/DOS/phonon/EPC/NEB calculations, run completion, reproducibility, and deciding whether a QE result is documented, comparable, and scientifically supportable.
---

# QE Rigorous Calculations

Separate official software behavior, input integrity, execution completion, numerical convergence, and physical validity. Never treat a QE default, a common recipe, or one completed run as scientific adequacy.

## Enforce the source boundary

- Use only `https://www.quantum-espresso.org/Doc/` and documents directly discovered there for official QE software claims.
- Read [references/official-manual-index.md](references/official-manual-index.md), then only the executable, parameter, guide page, release note, or PDF page needed.
- Match the manual version to the version printed by the relevant executable. Apply the version gate in the official index when they differ.
- Recheck the recorded official URL for version-sensitive behavior whenever network access is available.
- Label project observations and current analysis separately. Do not store project experience in this skill.
- Never convert a default into a convergence claim or reproduce a local pseudopotential file as documentation.

## Version Gate

1. Read the QE version printed by the relevant executable output.
2. Read the manual version from the executable-specific official index.
3. Use exact syntax, defaults, and restrictions only when the versions match.
4. If they differ, do not project the current manual backward. Use release notes only for changes they explicitly document.
5. State: `Exact behavior for QE <version> is not verified by a matching official input manual in this mirror.`
6. Treat a mixed-version official snapshot explicitly; one newer manual does not change the version of another mirrored manual.

## Choose the workflow

1. For a parameter question, identify executable, version, namelist/card, task stage, and interacting fields; read the exact official entry.
2. For calculation design, define the target observable and tolerance first; read [references/calculation-workflow.md](references/calculation-workflow.md).
3. For input audit, check syntax and cross-stage prerequisites against the matching official manuals.
4. For output audit, inspect completion, warnings, convergence, actual echoed settings, forces/stress, and downstream ancestry.
5. For numerical convergence, vary controlled inputs against the quantity used in the scientific claim; require a stable tail or justified multidimensional study.
6. At completion, stop, failure, or scientific acceptance, emit a run manifest and hand it to `$dft-campaign-efficiency`; do not maintain experience here.

## Establish provenance

Record or mark missing:

- QE executable versions and build identity;
- scientific objective, task type, observable, tolerance, and acceptance/stop criteria;
- structure source, pseudopotential filenames plus non-sensitive hashes/metadata, XC treatment, spin/SOC/Hubbard/dispersion settings, constraints, and boundary conditions;
- exact inputs, k/q meshes, workflow stage, prefix/outdir ancestry, and restart lineage;
- scheduler/runtime metrics when available.

Do not invent missing provenance. Do not expose credentials, hosts, accounts, private absolute paths, or unpublished results in the skill source.

## Verify documented behavior

For every decisive field:

- state official type, default, units, allowed values, prerequisites, and restrictions when documented;
- cite the exact official URL and mirrored retrieval metadata;
- state any executable/manual version mismatch before version-sensitive conclusions;
- write `Not specified by the official QE manual` when the source is silent;
- report official-document conflicts rather than silently selecting one.

## Verify scientific support

- Define convergence for a named observable and tolerance.
- Hold irrelevant choices fixed across comparisons.
- Check basis, k/q sampling, smearing, electronic/ionic thresholds, finite-size controls, interpolation/direct calculations, and model choices when relevant.
- Keep Gamma-only, line-path, regular q-mesh, Fourier interpolation, and direct checkpoint evidence distinct.
- Keep syntax validity, completed execution, numerical convergence, and physical validation as separate statuses.
- Never call a result `converged` without naming observable, tolerance, series, and fixed protocol.

## Produce the run handoff

After a terminal calculation event, create `run_manifest.json` with the canonical [run manifest contract](../../contracts/run-manifest.schema.json):

```bash
python3 ../../tools/create_run_manifest.py \
  --code qe --code-version <VERSION> --task-type <TASK> \
  --case-id <ANONYMIZED_ID> --protocol-id <PROTOCOL_ID> \
  --status <STATUS> --scientific-acceptance <ACCEPTANCE> \
  --out run_manifest.json
```

Use an anonymized case id. Record unavailable metrics as null or omit optional properties; do not fabricate them. Send accepted or terminal records to `$dft-campaign-efficiency`. Send outputs requiring extraction or figures to `$dft-postprocess`.

## Maintain the official mirror

Use the bundled transactional mirror scripts:

```bash
python3 scripts/sync_official_manuals.py --refresh
python3 scripts/test_sync_official_manuals.py
python3 scripts/sync_official_manuals.py --check
```

A failed refresh must leave the prior validated mirror intact. Do not mix project experience into `references/`.

## Answer format

Lead with the actionable conclusion, then provide:

1. official QE facts and exact sources;
2. observed input/output evidence;
3. numerical-convergence and physical-validity assessment;
4. missing evidence and the smallest next calculation set;
5. version, pseudopotential, parser, or source limitations;
6. postprocessing and efficiency handoffs when applicable.
