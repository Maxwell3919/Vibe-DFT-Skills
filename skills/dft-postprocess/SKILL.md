---
name: dft-postprocess
description: Inventory, extract, normalize, validate, analyze, and plot Quantum ESPRESSO or VASP results with deterministic Python tools and optional external DFT-tool adapters. Use for run-output inspection, energy/force/SCF traces, bands, DOS/PDOS, phonon, EPC, work-function and other derived data, tool availability checks, provenance, publication figures, artifact manifests, and deciding whether a postprocessed result is complete and traceable.
---

# DFT Postprocess

Produce structured data before figures. Treat parsing, numerical analysis, visualization, and scientific interpretation as separate stages. Never infer a numerical conclusion from plot appearance alone.

## Start with inventory and contracts

1. Identify the source run, code/version, task, expected outputs, and `run_manifest.json` when available.
2. Run `python3 scripts/dftpost_cli.py inventory <RUN_DIR> --out inventory.json`.
3. Run `python3 scripts/dftpost_cli.py capabilities --out capabilities.json` before selecting external tools.
4. Read [references/observable-registry.yaml](references/observable-registry.yaml) for the machine-tracked route and maturity, then [references/observable-matrix.md](references/observable-matrix.md) for the compact human overview.
5. Read [references/tool-registry.md](references/tool-registry.md) before invoking a QE/VASP ecosystem tool.
6. Read [references/validation-data-policy.md](references/validation-data-policy.md) before using real local or remote calculation artifacts for validation.

Do not install tools automatically. Return `TOOL_UNAVAILABLE` with the missing executable/package, intended operation, and fallback boundary.

## Keep implementations general

- Implement only reusable parsing, normalization, validation, numerical analysis, and plotting behavior.
- Parameterize species, atom or layer groups, energy windows, band or mode selections, path labels, thresholds, and comparison rules when they are legitimate workflow inputs.
- Do not encode a material name, project directory, campaign layout, selected case, hand-picked index, project-specific threshold, or case-specific physical conclusion in the skill library.
- Keep one-off physical interpretation and material-specific analysis in the project processing area. Promote it only after separating the general algorithm from case configuration and adding transferable tests.
- Report generic computed facts separately from material-specific scientific interpretation; do not add the latter to bundled scripts.

## Execute the evidence pipeline

Use this order:

1. inventory immutable source evidence;
2. extract normalized JSON/CSV with units and energy reference;
3. validate completeness, dimensions, labels, finite values, and provenance;
4. perform deterministic numerical analysis;
5. plot only validated structured data;
6. emit `artifact_manifest.json` using the canonical [artifact contract](../../contracts/artifact-manifest.schema.json);
7. report supported claims, limitations, and blocked claims.

For QE/VASP scalar traces:

```bash
python3 scripts/dftpost_cli.py extract-summary <OUTPUT> --code auto --out summary.json
```

## Use the normalized workflow entry points

The bundled CLI routes all implemented workflows through normalized CSV/JSON, semantic checks, plot metadata, and explicit overwrite protection:

| Workflow | Entry point | Required explicit evidence |
|---|---|---|
| SCF/relax trace | `run-trace` | code and main output |
| QE bands/DOS/fatband | `qe-bands`, `qe-dos`, `qe-fatband` | energy reference; projection selector for fatband |
| VASP bands/DOS/fatband | `vasp-bands`, `vasp-dos`, `vasp-fatband` | EIGENVAL/DOSCAR/PROCAR plus structure, path, and reference files as applicable |
| Combined bands + DOS | `bands-dos` | normalized bands/DOS tables and optional channels/window |
| QE phonon/EPC | `qe-phonon`, `qe-epc` | frequency unit; alpha2F/lambda inputs and explicit smearing selections |
| Grid/ELF/potential | `grid-field` | code, field kind, field unit, averaging axis; work function additionally needs conversion, Fermi reference, and vacuum window |
| Bader ACF | `bader-acf` | code and ACF; optional per-atom reference electron values |
| Generic NEB/optical | `neb-table`, `optical-table` | caller-mapped columns, units/reference or component/broadening declarations |

Use `--overwrite` only for an intentional atomic replacement of derived files. Raw inputs are never overwrite targets.

For a machine-generated plan, supply file evidence with `--evidence role=relative/path` and non-file semantics with `--parameter name=value`. Missing required parameters block the plan; the planner must not emit placeholders that look executable.

Treat maturity in the observable registry literally. `synthetic-validated` proves internal contracts and arithmetic, not native QE/VASP format compatibility. Only `real-artifact-validated` routes have passed a real-artifact forward test.

For a normalized table:

```bash
python3 scripts/dftpost_cli.py plot-table data.csv \
  --x energy_ev --y dos_states_per_ev --xlabel 'Energy (eV)' \
  --ylabel 'DOS (states/eV)' --out dos.png --metadata-out dos.plot.json
```

Validate any manifest:

```bash
python3 scripts/dftpost_cli.py validate-manifest artifact artifact_manifest.json
```

## Protect provenance and privacy

- Preserve source labels, checksums, code/tool versions, command arguments, units, reference energies, spin/channel mapping, and transformations.
- Write artifact paths relative to the artifact root.
- Never copy POTCAR contents, raw private calculation trees, credentials, hosts/accounts, or project identifiers into this skill.
- Do not overwrite raw outputs. Write derived data and figures to a separate processing directory.
- Mark missing, partial, failed, redacted, and external evidence explicitly.
- Use user-authorized remote calculation artifacts read-only. Read the applicable host and project rules first, copy only the minimum evidence needed, and keep real host names, paths, values, and raw artifacts outside the committed skill repository.

## Validate figures

Follow [references/plotting-and-evidence-standard.md](references/plotting-and-evidence-standard.md).

- Bind every curve to a structured column and unit.
- State energy zero/reference, normalization, broadening, interpolation, aggregation, and spin convention.
- Check axes, labels, legend, dimensions, finite values, output existence, and metadata.
- Treat PNG/PDF/SVG as presentation artifacts; use CSV/JSON and numerical checks for claims.
- Do not hide warnings, imaginary modes, missing channels, incomplete ranges, or failed calculations.
- Display every completed validation figure directly to the user after visual QA; do not merely report that a file was written.
- Give line plots exact horizontal data limits and zero horizontal margin. Use deep red `#7f1d1d` for primary band/path curves unless another mapping is required.

## Route interpretation

- Report direct computed facts only when structured data and validation support them.
- Label current analysis and scientific interpretation separately.
- Route calculation-integrity questions to `$qe-rigorous-calculations` or `$vasp-rigorous-calculations`.
- Route accepted terminal metrics to `$dft-campaign-efficiency`.
- Use `BLOCK` when required source evidence, units, mapping, or provenance is absent.

## Output format

Return:

1. source inventory and tool route, including the actual runtime host/path and a compact source-data preview when the user authorized access;
2. generated structured data and checks;
3. every generated result table and every figure, with figures embedded from their absolute local paths after visual QA;
4. artifact-manifest status (`pass`, `warn`, or `block`);
5. supported facts, limitations, and smallest next action.

Do not call a real-data validation complete until the response shows its source evidence, numerical result, and all generated figures. If a workflow produces no figure, state that explicitly.
