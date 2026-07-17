---
name: vasp-rigorous-calculations
description: Design, explain, audit, troubleshoot, and validate rigorous VASP calculations using official VASP Wiki documentation for software behavior and observable-specific numerical evidence for scientific convergence. Use for INCAR, POSCAR, KPOINTS, POTCAR metadata, VASP input/output review, relax/static/band/DOS/phonon/NEB/defect/surface/magnetic/SOC/DFT+U/hybrid/GW workflows, convergence studies, reproducibility, completion, comparability, and scientific support.
---

# VASP Rigorous Calculations

Treat documented syntax, structural/file integrity, completed execution, numerical convergence, and physical validity as separate gates. Never turn a default, common recipe, or successful run into evidence of adequacy.

## Enforce the source boundary

- Use `https://www.vasp.at/wiki/` and pages retrieved through its official MediaWiki API for official VASP claims.
- Read [references/official-wiki-index.md](references/official-wiki-index.md), then only the required pages.
- Recheck live official pages for version-sensitive behavior whenever network access is available.
- Match documentation to the VASP version printed in `OUTCAR` or `vasprun.xml`; state historical ambiguity.
- Inspect only non-sensitive POTCAR metadata needed for the user's case. Never reproduce or commit licensed POTCAR contents.
- Label code observations, project evidence, and scientific judgment separately.

## Choose the workflow

1. For a tag/file question, identify version, task stage, interacting tags, and exact official page.
2. For calculation design, define observable and tolerance; read [references/rigor-protocol.md](references/rigor-protocol.md) and [references/task-checklists.md](references/task-checklists.md).
3. For a case audit, run `python3 scripts/audit_vasp_case.py CASE --pretty`; treat parser limitations explicitly.
4. For convergence, run `scripts/analyze_convergence.py` on a controlled series; its candidate is numerical evidence, not physical proof.
5. At completion, stop, failure, or scientific acceptance, emit `run_manifest.json` for postprocessing and efficiency handoff.

## Establish provenance

Record or mark missing:

- VASP version/build and task/observable/tolerance;
- structure source, charge/spin state, constraints, and boundary conditions;
- XC method and all corrections;
- POTCAR dataset order plus non-sensitive `TITEL`, `LEXCH`, `ENMAX`, release label, and local SHA-256;
- exact `INCAR`, `POSCAR`, `KPOINTS` or `KSPACING`, stage, and restart ancestry;
- scheduler/runtime metrics when available.

Do not invent missing values or publish private paths, hosts, accounts, output trees, or POTCAR contents.

## Verify input and execution integrity

Check:

- POSCAR lattice, species/counts, coordinate mode, coordinate row count, numerical coordinates, and selective-dynamics flags;
- POSCAR species order against POTCAR dataset order;
- KPOINTS mode, declared count, mesh positivity, shift, line-mode/explicit rows, or valid `KSPACING` alternative;
- explicit basis, sampling, occupation, electronic, ionic, spin, and correction choices relevant to the claim;
- restart files required by `ISTART`, `ICHARG`, and workflow ancestry;
- output completion, warnings, electronic/ionic convergence, forces/stress, and echoed settings;
- downstream use of the intended structure, density, wavefunctions, and method.

The auditor must reject malformed structure and sampling inputs. Never downgrade a parse failure to a clean audit.

## Build scientific convergence evidence

- Define the named observable and tolerance.
- Vary one numerical control at a time unless an interaction study is intentional.
- Include enough points for nonmonotonic behavior and a stable tail.
- Consider basis/FFT precision, k/q sampling, occupations, electronic/ionic thresholds, finite-size controls, spin/SOC/U/dispersion/hybrid settings, and task-specific model controls.
- Verify comparability before energy/property comparisons, including compatible POTCAR datasets.

Use evidence labels: `officially documented`, `observed in output`, `numerically converged for <observable> within <tolerance>`, `physically validated`, `assumption`, and `unresolved`.

## Produce the run handoff

Create a canonical [run manifest](../../contracts/run-manifest.schema.json):

```bash
python3 ../../tools/create_run_manifest.py \
  --code vasp --code-version <VERSION> --task-type <TASK> \
  --case-id <ANONYMIZED_ID> --protocol-id <PROTOCOL_ID> \
  --status <STATUS> --scientific-acceptance <ACCEPTANCE> \
  --out run_manifest.json
```

Send output extraction/figures to `$dft-postprocess`. Send terminal run metrics to `$dft-campaign-efficiency`; do not store project experience here.

## Maintain the official mirror

```bash
python3 scripts/sync_official_wiki.py --refresh --scope core
python3 scripts/test_skill_scripts.py
python3 scripts/sync_official_wiki.py --check
```

Refresh into staging, validate it, replace the old mirror only after success, and reject stale pages outside the manifest.

## Answer format

Lead with the actionable conclusion, then provide documented VASP facts, observed evidence, convergence/physical assessment, missing evidence and smallest next calculation set, and source/POTCAR/parser limitations.
