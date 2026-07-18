# CP2K task and observable evidence

Read only the relevant row and its notes. The machine-readable counterpart is `task-evidence-profiles.json`.

| Task | Decisive input | Required run/derived evidence | Minimum scientific checks |
|---|---|---|---|
| Static energy/force/stress | `GLOBAL`, Quickstep core, requested print/control sections | main output; force/stress artifact when claimed | basis/grid/SCF/k-point/cell and state convergence |
| GEO_OPT | `RUN_TYPE GEO_OPT`, `MOTION/GEO_OPT`, constraints | completion marker, final structure, force history | force threshold, max step, constraints, final static parent |
| CELL_OPT | `RUN_TYPE CELL_OPT`, `MOTION/CELL_OPT` | completion marker, final cell/structure, force and stress history | stress/force threshold, cell degrees, Pulay/numerical convergence |
| MD | `RUN_TYPE MD`, `MOTION/MD`, ensemble controls | main output, trajectory, energy file, restart lineage | timestep, ensemble diagnostics, equilibration, sampling uncertainty |
| Bands | ENERGY parent plus `DFT/PRINT/BAND_STRUCTURE` | parent audit, `.bs`/normalized table, k-path labels | dense parent settings, energy reference, path and state continuity |
| DOS/PDOS | ENERGY parent plus version-specific DOS/PDOS print section | parent audit, total/projected files, reference energy | mesh/states/smearing/broadening, projection closure and units |
| Vibrations | `RUN_TYPE VIBRATIONAL_ANALYSIS` and analysis controls | frequencies/modes and child-force evidence | displacement, force tolerance, symmetry, supercell/boundary, ASR policy |
| BAND/NEB | `RUN_TYPE BAND`, `MOTION/BAND`, replicas | every image, energy/force history, endpoint hashes | image mapping, optimizer/springs, all-image convergence, saddle check |

## Parent-child binding

For derived electronic or response tasks, bind the child to:

- parent case/run id and audit SHA-256;
- input and expanded-input hashes;
- cell/coordinates and charge/spin state;
- basis/potential/XC/correction definitions;
- k-point, SCF, occupation and restart settings;
- code version/build and protocol id.

Any unplanned Hamiltonian change creates a new comparability group.

## Molecular dynamics

Do not accept MD from normal termination alone. Record ensemble, thermostat/barostat, timestep, masses, constraints, seed, initialization, total steps/time, restart joins, equilibration exclusion, production window and statistical uncertainty. Check for duplicated frames after restarts before time-series analysis.

## Geometry and cell optimization

Separate optimizer termination from scientific adequacy. Inspect final and maximum force, stress when applicable, maximum displacement/step, constraints, boundary conditions and state continuity. Re-run a controlled static calculation on the final structure when it will parent a property calculation.

## Vibrations and transition paths

Inventory every displacement or replica. A primary output without complete child evidence cannot support a complete Hessian, mode set, barrier or saddle claim. Report imaginary modes and unconverged images explicitly.
