# QE calculation workflow and evidence gates

Use [fail-closed-contract.md](fail-closed-contract.md) for commands, exit codes, and mandatory blocking semantics. This file identifies scientific evidence; it does not override a failed deterministic gate.

## Gate sequence

1. Create `qe_plan.json` with the target observable, unit, tolerance, QE version, and anonymous protocol id. Stop if any value would have to be invented.
2. Identify every executable stage and resolve each decisive field to one version-matching official manual entry.
3. Run the deterministic `pw.x` input gate where applicable; mark other executable inputs `not automated` and audit them manually from official sources.
4. Validate structure, pseudopotential identity, basis, sampling, occupations, spin, corrections, constraints, and restart ancestry.
5. Obtain explicit execution authorization; do not make job submission an implicit consequence of input design.
6. Audit outputs for version, fatal markers, completion, actual echoed settings, electronic/ionic convergence, and ancestry.
7. Build observable-specific numerical convergence evidence under one unchanged plan and fixed protocol. Bind every point to a distinct passing QE input/output audit and verify the underlying file hashes.
8. Perform model/physics checks required by the bounded claim. A stable numerical tail is not this gate.
9. Emit `run_manifest.json`; route numerical extraction to postprocessing and terminal metrics to campaign efficiency.

## Common task evidence

| Task | Minimum integrity evidence | Numerical evidence that remains required |
|---|---|---|
| SCF/static | completed output, charge convergence, actual settings, energy/forces/stress as relevant | basis, k mesh, occupation, electronic threshold for target observable |
| relax/vc-relax | completed/stop reason, final structure, forces/stress, constraints, restart lineage | force/stress thresholds, basis/k mesh, Pulay and cell sensitivity |
| bands/DOS | technically completed parent density plus a bundle-verified human decision chain, fixed method, path/mesh provenance, energy reference | parent SCF convergence, band count, DOS grid/broadening, projection completeness |
| phonon | converged ground state, q provenance, acoustic/NAC/2D treatment where relevant | q mesh, electronic thresholds, interpolation vs direct checkpoints, supercell/model controls |
| EPC | complete electronic and phonon ancestry, k/q mesh pairing, smearing/integration method | nested mesh or controlled convergence of the reported coupling/Tc observable |
| NEB | endpoint provenance, image mapping, force/status evidence | image count, path initialization, force tolerance, endpoint and supercell convergence |

No row supplies universal numerical values. Define tolerances from the target scientific claim.

## Fail-closed interpretation

- Keep `input_integrity`, `pseudopotential_provenance`, `official_version_match`, `parent_ancestry`, `execution_completion`, `observable_convergence`, and `physical_validity` as separate statuses.
- Allow `pass`, `fail`, `incomplete`, and `not_assessed`; never coerce the last two to `pass`.
- Treat the allowlisted `pw.x` guard coverage as a lower bound. It blocks syntax outside its core and does not validate every QE feature, independently verify a declared pseudopotential source, establish pseudopotential quality, cover every cross-stage invariant, or make a final physical interpretation.
- Require a new convergence record when the observable, tolerance, structure, pseudopotential family, XC/spin/SOC/Hubbard/dispersion model, boundary condition, or other fixed protocol changes materially.
- Reject a convergence point when its CSV value, plan, audited setting, parsed output observable, input hash, output hash, or audit hash does not agree. Do not reuse one run for multiple settings.
- Report the smallest evidence-producing next calculation, not a generic request to “converge better.”
