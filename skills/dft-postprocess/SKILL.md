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
4. Read [references/observable-matrix.md](references/observable-matrix.md) for the observable-specific route.
5. Read [references/tool-registry.md](references/tool-registry.md) before invoking a QE/VASP ecosystem tool.

Do not install tools automatically. Return `TOOL_UNAVAILABLE` with the missing executable/package, intended operation, and fallback boundary.

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

## Validate figures

Follow [references/plotting-and-evidence-standard.md](references/plotting-and-evidence-standard.md).

- Bind every curve to a structured column and unit.
- State energy zero/reference, normalization, broadening, interpolation, aggregation, and spin convention.
- Check axes, labels, legend, dimensions, finite values, output existence, and metadata.
- Treat PNG/PDF/SVG as presentation artifacts; use CSV/JSON and numerical checks for claims.
- Do not hide warnings, imaginary modes, missing channels, incomplete ranges, or failed calculations.

## Route interpretation

- Report direct computed facts only when structured data and validation support them.
- Label current analysis and scientific interpretation separately.
- Route calculation-integrity questions to `$qe-rigorous-calculations` or `$vasp-rigorous-calculations`.
- Route accepted terminal metrics to `$dft-campaign-efficiency`.
- Use `BLOCK` when required source evidence, units, mapping, or provenance is absent.

## Output format

Return:

1. source inventory and tool route;
2. generated structured data and checks;
3. figures and visual QA;
4. artifact-manifest status (`pass`, `warn`, or `block`);
5. supported facts, limitations, and smallest next action.
