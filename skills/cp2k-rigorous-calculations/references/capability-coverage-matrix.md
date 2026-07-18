# CP2K capability and evidence coverage

Use this matrix to decide the strongest conclusion the skill may emit. Do not infer support from a topic appearing in the official mirror.

## Maturity vocabulary

- `deterministic-core`: bundled code parses the declared surface and has positive and negative tests.
- `evidence-profile`: bundled code detects the surface and enforces a task/method evidence profile, but scientific review remains mandatory.
- `official-routed`: version-matched official material is available; the bundled code does not validate the full surface.
- `design-only`: workflow is described but lacks sufficient parser or forward-test evidence.
- `blocked`: the skill must not produce a positive conclusion.

## Current coverage

| Domain | Official source | Input audit | Output audit | Scientific gate |
|---|---|---|---|---|
| One Quickstep `FORCE_EVAL`, explicit inline cell/coordinates | cached + live resolver | deterministic-core | static synthetic-positive plus CP2K-9 sanitized negative format fixture | blocked pending convergence/model evidence |
| Project, RUN_TYPE, basis/potential declarations and supplied data hashes | cached + live resolver | deterministic-core identity gate | deterministic input-output binding without emitting names | appropriateness requires independent review |
| MGRID/SCF/XC/periodicity core | cached + live resolver | deterministic-core syntax/profile | generic SCF markers; CP2K-9 format exercised | observable-specific convergence required |
| ENERGY/ENERGY_FORCE | cached + live resolver | task profile | static technical gate | force/stress/property validation remains separate |
| GEO_OPT/CELL_OPT | cached + live resolver | task/run-type section profile | synthetic completion marker plus required evidence roles | final forces/stress and static parent required |
| MD | cached + live resolver | task/keyword profile | evidence inventory only; completion validator blocked | ensemble diagnostics, equilibration and uncertainty required |
| Band structure and DOS/PDOS | cached + live resolver | task/section profile | evidence inventory only; completion validator blocked | parent density, reference energy and convergence required |
| Vibrational analysis | cached + live resolver | task/section profile | evidence inventory only; completion validator blocked | displacement/force/supercell validation required |
| BAND/NEB | cached + live resolver | task/section profile | image/replica inventory only; completion validator blocked | all-image forces and saddle validation required |
| OT, diagonalization, smearing, k-points, restart | cached + live resolver | detected; automated pass blocked outside core | not deterministically validated | state and convergence review required |
| Hybrid/HFX, ADMM, DFT+U, dispersion, SCCS | cached + live resolver | detected; automated pass blocked outside core | not deterministically validated | method-specific numerical evidence required |
| MP2/RPA/GW, TDDFPT/XAS, RTP, transport | cached + live resolver | official-routed | design-only | blocked from automated positive claim |
| QM/MM, FIST/MM, metadynamics, path integrals | cached + live resolver | official-routed | design-only | blocked from automated positive claim |
| Multiple `FORCE_EVAL`, preprocessing/includes without external validator | cached + live resolver | blocked | blocked | blocked |

## Completion definition

A domain may move to `deterministic-core` only when all are present:

1. exact stable-version official pages and source hashes;
2. explicit parser boundary and machine-readable task/method profile;
3. positive input fixture and at least one negative fixture per decisive invariant;
4. privacy-safe output schema and stable finding codes;
5. real CP2K forward fixture or an explicit `no-real-artifact-validation` limitation;
6. observable-specific convergence and physical/model gates;
7. run-manifest and postprocess handoff tests.

The checked-in forward fixture is derived from a public CP2K 9.0-development output in the official `cp2k-output-tools` repository, pinned by commit and source hash, then privacy-sanitized under its MIT license. It exercises legacy output markers and the runtime/MPI-warning blocker. Its maturity ceiling is `format-fixture-validated`; it is neither a CP2K 2026.2 positive run nor untouched real-artifact validation.

File count and prose volume are not maturity evidence.
