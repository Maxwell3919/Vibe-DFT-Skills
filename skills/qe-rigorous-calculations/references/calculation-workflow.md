# QE calculation workflow and evidence gates

## Gate sequence

1. Define the scientific observable, tolerance, model, and acceptance criteria.
2. Identify the QE executable chain and version at every stage.
3. Validate input grammar and cross-stage prerequisites from official manuals.
4. Validate structure, pseudopotential identity, basis, sampling, occupations, spin, corrections, constraints, and restart ancestry.
5. Confirm clean completion and actual settings from outputs.
6. Build observable-specific numerical convergence evidence.
7. Perform model/physics checks required by the claim.
8. Emit `run_manifest.json`; route numerical extraction to postprocessing and terminal metrics to campaign efficiency.

## Common task evidence

| Task | Minimum integrity evidence | Numerical evidence that remains required |
|---|---|---|
| SCF/static | completed output, charge convergence, actual settings, energy/forces/stress as relevant | basis, k mesh, occupation, electronic threshold for target observable |
| relax/vc-relax | completed/stop reason, final structure, forces/stress, constraints, restart lineage | force/stress thresholds, basis/k mesh, Pulay and cell sensitivity |
| bands/DOS | converged parent density, fixed method, path/mesh provenance, energy reference | parent SCF convergence, band count, DOS grid/broadening, projection completeness |
| phonon | converged ground state, q provenance, acoustic/NAC/2D treatment where relevant | q mesh, electronic thresholds, interpolation vs direct checkpoints, supercell/model controls |
| EPC | complete electronic and phonon ancestry, k/q mesh pairing, smearing/integration method | nested mesh or controlled convergence of the reported coupling/Tc observable |
| NEB | endpoint provenance, image mapping, force/status evidence | image count, path initialization, force tolerance, endpoint and supercell convergence |

No row supplies universal numerical values. Define tolerances from the target scientific claim.
