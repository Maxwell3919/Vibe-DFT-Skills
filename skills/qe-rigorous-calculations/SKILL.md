---
name: qe-rigorous-calculations
description: Design, explain, audit, troubleshoot, and validate rigorous Quantum ESPRESSO calculations with fail-closed deterministic gates, official documentation discovered under quantum-espresso.org/Doc/, and observable-specific numerical evidence. Use for QE input parameters, defaults, units, prerequisites, pw.x/ph.x/neb.x workflows, convergence studies, relax/static/bands/DOS/phonon/EPC/NEB calculations, pseudopotential provenance, run completion, restart ancestry, reproducibility, and deciding whether a QE result is documented, comparable, and scientifically supportable.
---

# QE Rigorous Calculations

Separate objective definition, official behavior, input integrity, pseudopotential provenance, execution completion, numerical convergence, and physical validity. Never treat a QE default, a common recipe, one completed run, or one stable scalar as scientific adequacy.

## Run deterministic gates first

- Read [references/fail-closed-contract.md](references/fail-closed-contract.md) for every calculation design, input/output audit, or convergence task.
- Resolve the bundled `scripts/qe_guard.py` from this skill directory; never assume the user's calculation directory is the skill directory.
- Create `qe_plan.json` before scientific calculation design. Do not invent an observable, tolerance, version, or protocol id.
- Run `reference` for every decisive official parameter. Use `--live-check` when network access is available; use `--offline` only with an explicit cached-source limitation.
- Run `audit` before calling a `pw.x` input ready and again with both `--output` and the separately captured `--stderr` before calling its execution complete.
- Run `convergence` only on fixed-protocol tables whose rows bind the unchanged plan, distinct audit reports, and matching input/output content hashes; keep every untested convergence dimension explicit.
- Treat any nonzero exit, `decision != pass`, `fail`, `incomplete`, `not_assessed`, or `scientific_claim_decision: blocked` as a hard stop for the corresponding positive claim.
- Never edit a generated report or omit adverse evidence to make a gate pass.

The guard intentionally automates only a conservative, allowlisted `pw.x` core. Any unrecognized namelist, field, card, duplicate assignment, or arithmetic coordinate expression blocks an automated pass. For advanced `pw.x` features and for `ph.x`, `neb.x`, and other executables, retrieve the official entry, perform the manual workflow audit, and label the deterministic status `not automated`. A manual review may document the unsupported surface but cannot turn a failed guard into `input_ready` or a tool pass; extend and test the guard or retain the blocking status.

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

1. For a parameter question, identify executable, version, namelist/card, task stage, and interacting fields; run the official reference lookup before answering.
2. For calculation design, define the target observable and tolerance in the plan, then read [references/calculation-workflow.md](references/calculation-workflow.md).
3. Before writing or launching a command, read [references/execution-and-program-map.md](references/execution-and-program-map.md) for the real `pw.x`/`ph.x`/`neb.x` and postprocessing program ownership, input-file syntax, parent chain, and native-validation boundary.
4. For input audit, run the supported guard and check unsupported syntax/cross-stage prerequisites manually against matching official manuals.
5. Before execution, obtain explicit user authorization. Do not launch QE or submit a scheduler job merely because an input was requested.
6. For output audit, inspect completion, warnings, convergence, actual echoed settings, forces/stress, and downstream ancestry.
7. For numerical convergence, vary controlled inputs against the quantity used in the scientific claim; require a stable tail or justified multidimensional study, and reject manually entered values that are not bound to audited input/output files.
8. At each terminal technical event, emit an immutable pre-decision run manifest and hand privacy-safe cost evidence to `$dft-campaign-efficiency`; record later human acceptance or rejection only in a separate decision record and post-decision claim map.

## Establish provenance

Record or mark missing:

- QE executable versions and build identity;
- scientific objective, task type, observable, tolerance, and acceptance/stop criteria;
- structure source, pseudopotential filenames plus independently declared source URLs/expected hashes/metadata, XC treatment, spin/SOC/Hubbard/dispersion settings, constraints, and boundary conditions;
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
- Never call a result scientifically accepted while the guard reports `scientific_claim_decision: blocked`; resolve the remaining observable-specific and physical/model gates first.

## Produce the run handoff

After a terminal calculation event, create `run_manifest.json` against the registered canonical `run-manifest@1.0` interface:

```bash
python3 ../../tools/create_run_manifest.py \
  --code qe --code-version <VERSION> --task-type <TASK> \
  --case-id <ANONYMIZED_ID> --protocol-id <PROTOCOL_ID> \
  --status <STATUS> --scientific-acceptance <ACCEPTANCE> \
  --out run_manifest.json
```

Use an anonymized case id. Use `status=completed` with `scientific_acceptance=not_assessed` or `requires_human_review`; planned, running, stopped, and failed records must remain `not_assessed`. Never rewrite this manifest to `accepted` or `rejected`. Those outcomes require the downstream `calculation-record-envelope → human decision-record → postdecision claim-evidence-map` chain and production bundle verification. Record unavailable metrics as null or omit optional properties; do not fabricate them. Send terminal cost records to `$dft-campaign-efficiency`, and send outputs requiring extraction or figures to `$dft-postprocess`.

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
