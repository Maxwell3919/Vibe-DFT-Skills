---
name: dft-postprocess
description: Inventory, extract, normalize, validate, analyze, and plot DFT results with deterministic Python tools, native QE/VASP routes, explicit CP2K/SIESTA maturity gates, and optional external adapters. Use for run-output inspection, energy/force/SCF traces, bands, DOS/PDOS, phonon, EPC, work-function and other derived data, tool availability checks, provenance, publication figures, artifact manifests, and deciding whether a postprocessed result is complete and traceable.
---

# DFT Postprocess

Produce structured data before figures. Treat parsing, numerical analysis, visualization, and scientific interpretation as separate stages. Never infer a numerical conclusion from plot appearance alone.

## Start with inventory and contracts

1. Identify the source run, code/version, task, expected outputs, and `run_manifest.json` when available.
2. Run `python3 scripts/dftpost_cli.py inventory <RUN_DIR> --out inventory.json`.
3. Run `python3 scripts/dftpost_cli.py capabilities --out capabilities.json` before selecting external tools.
4. Read [references/observable-registry.yaml](references/observable-registry.yaml) for the machine-tracked route and maturity, then [references/observable-matrix.md](references/observable-matrix.md) for the compact human overview.
5. Read [references/tool-registry.md](references/tool-registry.md) before invoking a code-specific DFT ecosystem tool.
6. Read [references/validation-data-policy.md](references/validation-data-policy.md) before using real local or remote calculation artifacts for validation.

Do not install tools automatically. Return `TOOL_UNAVAILABLE` with the missing executable/package, intended operation, and fallback boundary.

## Keep implementations general

- Implement only reusable parsing, normalization, validation, numerical analysis, and plotting behavior.
- Parameterize species, atom or layer groups, energy windows, band or mode selections, path labels, thresholds, and comparison rules when they are legitimate workflow inputs.
- Do not encode a material name, project directory, campaign layout, selected case, hand-picked index, project-specific threshold, or case-specific physical conclusion in the skill library.
- Keep one-off physical interpretation and material-specific analysis in the project processing area. Promote it only after separating the general algorithm from case configuration and adding transferable tests.
- Report generic computed facts separately from material-specific scientific interpretation; do not add the latter to bundled scripts.
- Real-space scripts may expose generic plane, crop, color, isovalue, opacity, structure, and view parameters. Do not bundle case-specific arrows, panel letters, charge-transfer narratives, selected material labels, hand-tuned project thresholds, or paper-figure assembly.
- Treat structure-view connections, atom radii, colors, boundary images, and camera directions as recorded display mappings. Do not present a drawn connection as a calculated bond order or bonding conclusion.

## Execute the evidence pipeline

Use this order:

1. inventory immutable source evidence;
2. extract normalized JSON/CSV with units and energy reference;
3. validate completeness, dimensions, labels, finite values, and provenance;
4. perform deterministic numerical analysis;
5. plot only validated structured data;
6. emit `artifact_manifest.json` against the registered canonical `artifact-manifest@1.0` interface;
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
| VASPKIT band-table import | `vaspkit-bands` | `BAND.dat`/`REFORMATTED_BAND.dat`, `KLABELS`, explicit additive energy offset, and a reference description |
| Multi-system band comparison | `bands-compare` | two or more labeled normalized bands tables; optional matching plot metadata for path labels |
| Multi-channel projected bands | `band-projections` | one normalized bands table plus labeled, grid-aligned normalized fatband tables; separated panels are primary and an overlap overview is optional |
| Combined bands + TDOS/PDOS | `bands-dos` | normalized bands/DOS tables with typed total and projected channels; optional PDOS filters/window |
| Crystal top/side views | `structure-views` | one or more ASE-readable structures; explicit or recorded covalent graphical-connectivity mode and optional element display overrides |
| QE phonon/EPC | `qe-phonon`, `qe-epc` | frequency unit; alpha2F/lambda inputs and explicit smearing selections |
| Cube payload diagnosis | `cube-inspect` | one Cube file; reports the declared grid size, exact payload count, field count when divisible, and unsupported standard multi-dataset convention without assigning field semantics |
| Legacy concatenated Cube split | `cube-split` | a positive-atom-count Cube whose payload is an exact multiple greater than one of the declared grid size; outputs neutral indexed fields plus a hash-bearing manifest |
| Grid/ELF/potential/2D section | `grid-field` | code, field kind/unit, averaging axis; optional explicit `(hkl)`, offset, in-plane origin/window, atom overlay, colormap/range; work function additionally needs conversion, Fermi reference, and vacuum window |
| Linear grid combination | `grid-combine` | at least two explicit `coefficient=path` Cube components, common geometry, field unit, and structure-source component |
| Structure + 3D isosurfaces | `vesta-isosurface` | VESTA CLI, grid, field and isovalue units, positive/negative mode, explicit isovalue, colors/opacity, scale, and view rotation |
| Bader ACF | `bader-acf` | code and ACF; optional per-atom reference electron values |
| Generic NEB/optical | `neb-table`, `optical-table` | caller-mapped columns, units/reference or component/broadening declarations |

Use `--overwrite` only for an intentional atomic replacement of derived files. Raw inputs are never overwrite targets.

Run `cube-inspect` before normalizing any Cube whose payload length does not match its header. `grid-field` fails closed on concatenated payloads and reports the exact observed value count. `cube-split` is only a compatibility route for a positive-atom-count legacy file containing two or more complete fields; it does not split the standard negative-atom-count orbital/multi-dataset convention. Keep the generated `field-NNN.cube` names and manifest semantically neutral until independent calculation evidence establishes each field's meaning and unit. Only then use `grid-combine` with explicit coefficients.

For a machine-generated plan, supply file evidence with `--evidence role=relative/path` and non-file semantics with `--parameter name=value`. Missing required parameters block the plan; the planner must not emit placeholders that look executable.

Treat maturity in the observable registry literally and at the `observable × code × backend` level. `synthetic-validated` proves internal contracts and arithmetic, not native calculation-code format compatibility. `format-fixture-validated` proves only the pinned constructed format fixtures named by the route evidence record. No current backend has an immutable real-artifact or end-to-end tool receipt, so none may emit `real-artifact-validated` or `tool-integration-validated`. CLI and Python `maturity` arguments are downward claim ceilings, never caller-controlled promotion. A contract accepting `cp2k` or `siesta` is not evidence that a native parser exists.

For VASP non-self-consistent bands, use the energy reference from the scientifically matched parent calculation when that relationship is explicit in the evidence. Do not infer a parent SCF run from directory names or impose SCF `E-fermi` as an unconditional rule for every reference convention. `vaspkit-bands` never guesses what VASPKIT subtracted: require `energy_relative_ev = energy_input_ev + energy_offset_ev` and record the caller's reference description.

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
- Never copy POTCAR or other restricted potential contents, raw private calculation trees, credentials, hosts/accounts, or project identifiers into this skill.
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
- For QE line paths, pass each caller-verified label and sampled native coordinate to `qe-bands` as repeated `--symmetry-point LABEL=DISTANCE`; QE numeric coordinates alone do not establish Γ/X/M names. The normalizer must validate labels against sampled k-points and record them in analysis/plot metadata. Pass that `bands.plot.json` to `bands-dos --bands-metadata` so the combined figure hash-binds and renders the same high-symmetry ticks and guides.
- Define the `bands-dos` DOS panel as TDOS plus at least one PDOS channel. Select TDOS from `channel_type=total`, retain it when PDOS is filtered with `--pdos-channel`, and fail closed when typed total or projected evidence is absent.
- For QE PDOS, prefer the matching `prefix.pdos_tot` emitted by `projwfc.x` as `qe-dos --total` when atomic `prefix.pdos_atm#...` files are supplied. A separately generated `dos.x` table may use a different energy interval or point count; keep it as an independent TDOS artifact unless its grid aligns exactly. Never interpolate merely to force the PDOS gate to pass.
- Use separate projection panels as the primary view for multiple fatband selectors. Support both `bubble` area encoding and continuous `line-width` encoding; keep the overlap view optional, use a light neutral band background, assign channel colors deterministically, and record weight encoding and input hashes. In `bubble` mode use the explicit linear-area contract `marker_area_pt2 = marker_scale^2 * projection_weight`, with a translucent face and visible same-channel edge; never square the weight itself. In `line-width` mode start at zero width and use `line_width_pt = marker_scale * 0.45 * projection_weight`, so zero projection leaves only the neutral background band. Put both the caller-defined background-bands label and the caller label or selector-derived species/orbital label in every projected-band legend. Do not infer orbital dominance from visual overlap.
- For comparison figures, keep each dataset on its own axes, use the declared energy reference and path labels, lock each horizontal range to its own data endpoints, and state that visual panels alone do not establish cross-dataset comparability.
- For structure views, duplicate only crystallographically equivalent 0/1 boundary sites, depth-sort atoms and graphical connections, clip connections at display-sphere surfaces, and record whether connectivity was `none`, covalent-radius heuristic, or caller-explicit.
- For ELF sections, use the declared `electron-localization` field kind to default to a 0–1 `turbo` map; for declared charge-density differences, use a zero-centered diverging map. Treat `(hkl)`, offset, interpolation, atom-plane tolerance, crop window, and display range as recorded visualization inputs.
- For VESTA CLI output, require a stable valid PNG and a parseable `.vesta` project. Record the raw conversion/export exit behavior, density import path, project format version, isovalue unit, and VESTA's inverse-color convention for paired positive/negative surfaces.

## Route interpretation

- Report direct computed facts only when structured data and validation support them.
- Label current analysis and scientific interpretation separately.
- Route calculation-integrity questions to `$qe-rigorous-calculations`, `$vasp-rigorous-calculations`, `$cp2k-rigorous-calculations`, or `$siesta-rigorous-calculations`.
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
