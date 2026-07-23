# GROMACS 2026.3 operational planning and audit guide

Use this guide to plan and review a conventional GROMACS workflow before any provider execution. It is version-bound to GROMACS 2026.3 and does not attest that a native `gmx` binary or a real simulation has run in this repository.

## Contents

- [Evidence labels and official sources](#evidence-labels-and-official-sources)
- [End-to-end workflow](#end-to-end-workflow)
- [System preparation](#system-preparation)
- [MDP audit](#mdp-audit)
- [Preprocessing and execution](#preprocessing-and-execution)
- [Restart and segment lineage](#restart-and-segment-lineage)
- [Failure triage](#failure-triage)
- [Trajectory and analysis checks](#trajectory-and-analysis-checks)
- [Performance work](#performance-work)
- [Minimum handoff](#minimum-handoff)

## Evidence labels and official sources

Keep the following labels explicit:

- **Official behavior**: a fact summarized from the exact-version GROMACS 2026.3 documentation linked below.
- **Operational heuristic**: a practical investigation order, not an official default or a scientific acceptance threshold.
- **Project decision**: a model, ensemble, parameter, tolerance, seed, duration, or acceptance rule supplied and justified by the project.
- **Observed evidence**: output from an explicitly authorized, captured provider run. No such native evidence is bundled here.

Primary sources, checked as reachable on 2026-07-22:

- [Typical simulation flow](https://manual.gromacs.org/documentation/2026.3/user-guide/flow.html)
- [System preparation](https://manual.gromacs.org/documentation/2026.3/user-guide/system-preparation.html)
- [MDP options](https://manual.gromacs.org/documentation/2026.3/user-guide/mdp-options.html)
- [`gmx grompp`](https://manual.gromacs.org/documentation/2026.3/onlinehelp/gmx-grompp.html)
- [`gmx mdrun`](https://manual.gromacs.org/documentation/2026.3/onlinehelp/gmx-mdrun.html)
- [Managing long simulations](https://manual.gromacs.org/documentation/2026.3/user-guide/managing-simulations.html)
- [File formats](https://manual.gromacs.org/documentation/2026.3/reference-manual/file-formats.html)
- [Common errors](https://manual.gromacs.org/documentation/2026.3/user-guide/run-time-errors.html)
- [`mdrun` performance](https://manual.gromacs.org/documentation/2026.3/user-guide/mdrun-performance.html)

Use the exact command recipes in [task-recipes.json](task-recipes.json). The workflow below explains what must be decided and audited; it is not permission to run those commands.

## End-to-end workflow

### Official behavior

A conventional solvated biomolecular route uses topology/coordinate preparation, box definition, solvation, ion replacement, preprocessing with `gmx grompp`, and execution with `gmx mdrun`. Minimization and each equilibration or production phase are separate run inputs and outputs.

### Operational audit

Treat every arrow as a content-addressed lineage boundary:

1. Audit the source structure and intended chemistry.
2. Generate a force-field-complete topology and force-field-compatible coordinates.
3. Define a box justified by the physical model and finite-size plan.
4. Solvate and verify the topology molecule counts.
5. Preprocess the ionization state, replace the declared solvent group with ions, and verify counts and charge.
6. Minimize until the project-defined criterion is met without instability markers.
7. Equilibrate temperature, then pressure when an NPT phase is physically intended.
8. Start production only from an accepted parent state and immutable production MDP/topology.
9. Verify native files before transforming or concatenating them.
10. Analyze only predeclared observables with sampling and uncertainty gates.

Block progression when a phase lacks its exact input closure, TPR hash, `grompp` transcript, `mdrun` transcript/log, expected outputs, acceptance check, or parent record.

## System preparation

### Official behavior

- `gmx pdb2gmx` builds a topology from a supported residue/force-field database and makes chemistry-changing choices such as termini, protonation, and special bonds through options or interactive selections.
- `gmx editconf` can define or transform the simulation box.
- `gmx solvate` adds solvent and can update the topology solvent count.
- `gmx genion` replaces atoms or molecules in a selected group with monatomic ions and can update the topology.
- `gmx grompp` combines MDP, coordinates, topology, optional index, and optional checkpoint state into a TPR.

### Operational audit

Before `pdb2gmx`, inventory alternate locations, missing atoms/residues, chain breaks, termini, protonation/tautomer states, disulfides, metals, cofactors, ligands, crystallographic waters, and residue naming. Stop if the chosen force field does not cover every retained component. Do not treat a PDB file as a complete force-field model.

For topology generation, record:

- exact force-field family and release;
- water and ion model compatibility;
- every interactive answer or explicit selector;
- residue/name transformations and removed atoms;
- generated `.top`, `.itp`, restraint, and coordinate hashes;
- any custom parameters with source, license, units, atom-type order, and validation status.

For the box and solvent, record the box type, dimensions, solute-to-boundary rule, periodic axes, solvent coordinate source, inserted molecule count, and pre/post topology counts. The box is a scientific finite-size choice, not a cosmetic container.

For ions, bind the ionization TPR to the exact solvated topology and coordinates. Record the selected replacement group, ion names, target concentration/neutralization intent, seed when applicable, replaced solvent count, final molecule counts, and final total charge. Never silence a topology/count mismatch by editing only one artifact.

Operational heuristic: inspect the generated structure visually and with distance/contact checks after each chemistry-changing step. Treat visualization as a diagnostic, not as proof of topology correctness.

## MDP audit

### Phase identity

Require a distinct authored MDP and protocol ID for minimization, NVT equilibration, NPT equilibration, and production. Hash the authored MDP and the `mdout.mdp` emitted by the matching `grompp` separately. `mdout.mdp` records processed settings but does not justify them.

### Integrator, duration, and initial state

Audit `integrator`, `dt`, `nsteps`, initial time/step controls, `continuation`, constraint startup, and velocity generation together. Derive simulated duration from `dt * nsteps`; do not infer it from a filename.

- For a new stochastic start, record `gen-vel`, `gen-temp`, and `gen-seed` as a project decision.
- For checkpoint continuation, normally preserve full-precision checkpoint state, disable velocity regeneration, and record parent checkpoint identity.
- For minimization, audit the selected minimizer, force/step controls, and whether its method is compatible with constraints.

Operational heuristic: test a shorter time step when instability appears, but do not accept the final value merely because the crash disappears. Recheck energy drift or the target observable against a predeclared criterion.

### Temperature and pressure coupling

Audit `tcoupl`, `tc-grps`, `tau-t`, `ref-t`, and coupling cadence as one unit. Confirm that every atom belongs to the intended coupling group exactly once and that the chosen thermostat supports the claimed ensemble and dynamical observable.

Audit `pcoupl`, `pcoupltype`, `tau-p`, `ref-p`, and `compressibility` together with box geometry and periodicity. Distinguish an equilibration device from a production ensemble method. Berendsen pressure coupling does not generate the correct NPT volume fluctuations and cannot alone support a production NPT fluctuation claim.

Do not copy coupling constants between materially different systems. They are project decisions whose adequacy must be assessed from response time, stability, distributions, and the target observable.

### Constraints, PBC, and nonbonded settings

Audit `constraints`, `constraint-algorithm`, LINCS/SHAKE settings, virtual sites, hydrogen-mass changes, and time step together. A constraint warning is not evidence that only the constraint solver needs tuning.

Audit `pbc`, box vectors, molecule-whole assumptions, center-of-mass removal, and any wall/slab treatment. Do not use a trajectory-centering operation to redefine the simulated boundary condition.

Audit the complete nonbonded tuple:

- `cutoff-scheme`, `nstlist`, `rlist`, and `verlet-buffer-tolerance`;
- `coulombtype`, `rcoulomb`, PME/FMM or reaction-field controls;
- `vdwtype`, `rvdw`, switching/shift modifiers, and dispersion correction;
- neighbor-list update, energy calculation, and coupling cadences;
- topology combination rules, exclusions, 1-4 interactions, and long-range corrections.

Establish whether the pair-list buffer is user-fixed or derived from the Verlet buffer tolerance. Never transplant cutoffs from another force field without checking that force field's requirements. Test cutoff, mesh, and finite-size sensitivity when they can affect the claim.

### Output and observable readiness

Audit `nstlog`, `nstenergy`, coordinate/velocity/force output, compressed trajectory cadence and groups, checkpoint cadence, and disk estimate before launch. XTC stores compressed positions, not a full restart state. TRR fields depend on what was requested. A trajectory cannot support an observable whose required fields or cadence were never written.

Operational heuristic: write enough early diagnostic information to resolve startup instability, then use a separately justified production cadence. Do not tune output cadence after seeing a desired fluctuation without versioning the protocol.

## Preprocessing and execution

### `gmx grompp` gate

Retain the exact argv, stdin/selections, environment-affecting defines/include paths, authored MDP, coordinates, topology closure, index, optional checkpoint, stdout/stderr, exit code, `mdout.mdp`, optional processed topology, and TPR hash.

Treat every warning as a question that must be resolved against the exact manual and model. Do not use `-maxwarn` as readiness evidence. A TPR built after overriding warnings remains blocked until each warning is independently dispositioned.

Before `mdrun`, use `gmx dump` or `gmx report-methods` where appropriate to inspect the TPR-derived configuration. These tools expose content; they do not validate scientific choices.

### `gmx mdrun` gate

Capture the exact executable/build identity, argv, runtime resource map, TPR, optional `-cpi` checkpoint, `-deffnm` or explicit output names, stdout/stderr, exit code, log, checkpoint, final coordinates, energy and trajectory hashes.

Require a clean terminal state and the planned final step. A scheduler state, exit code zero, or final performance line alone does not establish convergence, equilibrium, or sampling sufficiency.

## Restart and segment lineage

### Official behavior

- `gmx mdrun -cpi` reads checkpoint state; output appending is the default when compatible output files and their checkpoint checksums match.
- `-noappend` writes part-numbered output instead of extending the original files.
- `gmx convert-tpr` can extend the run length without regenerating velocities.
- When MDP or topology settings change, `gmx grompp -t <checkpoint>` can transfer full-precision coordinates, velocities, and applicable state into a new TPR.
- Checkpoint continuation is the supported continuation route; a coordinate file alone does not carry the full algorithm state.

### Operational audit

Use append only when preserving the exact output set expected by the checkpoint. If any prior output was renamed, removed, edited, or partially copied, stop and either restore it or create a separately named non-appending segment. Never force append around a checksum mismatch.

For every continuation, record parent TPR/checkpoint/output hashes, last accepted step/time, new TPR hash, append policy, expected first/last step, resource/build changes, and algorithm state known not to be exact. A portable checkpoint is not a promise of bitwise identity across compiler, hardware, rank/thread/GPU layout, load balancing, or unsupported feature changes.

Concatenate trajectories or energies only after verifying segment time ranges, atom order, box semantics, precision, overlaps, and gaps. Preserve raw segments and record the exact `trjcat` or `eneconv` selections/options and output hash.

## Failure triage

Use this order after preserving the failing inputs and full log. The causes below are diagnostic branches, not automatic fixes.

| Symptom | First evidence to inspect | Blocked shortcuts | Operational next checks |
|---|---|---|---|
| `grompp` atom/coordinate count mismatch | topology `[ molecules ]`, all includes, coordinate atom count, latest solvation/ion step | hand-editing only the reported count | compare the exact topology/coordinate lineage and rerun the first divergent preparation step |
| missing atom type, residue, or bonded parameter | preprocessed topology, force-field release, residue/atom naming, custom include order | substituting a similar-looking type | establish a sourced parameterization or remove the unsupported component from scope |
| nonzero total charge warning | intended charge state, protonation, ionization recipe, PME/electrostatics plan | blanket `-maxwarn` | decide whether charge is physical, a preparation error, or requires explicit correction/finite-size treatment |
| non-finite force during minimization | minimum distances, periodic contacts, units, topology/parameters | only increasing minimization steps | repair overlaps or parameters; then restart minimization as a new artifact |
| LINCS/SETTLE/SHAKE warning | coordinates near failure, temperature/energy trace, time step, constraints, topology | only increasing LINCS order | inspect bad contacts, force constants, units, equilibration, time step, and external forces |
| energy/temperature/pressure blow-up | first divergent step, potential components, box, coupling, neighbor/cutoff settings | suppressing the warning or continuing production | reproduce in a short diagnostic segment and isolate geometry, model, integration, or coupling causes |
| domain-decomposition/PME cell error | rank layout, box size, largest cutoff/interaction/constraint span, log decomposition report | changing scientific cutoffs only to fit more ranks | reduce parallel decomposition or validate an alternative resource layout before changing the model |
| run active but expected output absent | output cadences, last log step, disk/quota, buffering, NaN slowdown, scheduler stdout | assuming progress from CPU utilization | verify log freshness and files without altering the active output tree |
| append/checksum refusal | checkpoint metadata and exact prior output set | deleting or editing the checkpoint/output | restore the bound outputs or create a `-noappend` segment with explicit lineage |

If an error disappears under a different rank/GPU layout, report that as a reproduction clue. Do not automatically label the original trajectory physically invalid or the new one scientifically accepted.

## Trajectory and analysis checks

### Native integrity

- Run `gmx check` on each trajectory and energy artifact to inventory frames, times, fields, and detectable discontinuities.
- Use `gmx dump` for exact native metadata when required and version-match the reader.
- Compare the observed first/last time, frame cadence, atom count, field availability, and box against the plan and run log.
- Verify segment overlaps and gaps before concatenation.

### PBC and transforms

Preserve the raw trajectory. Record every `gmx trjconv` fit group, output group, centering choice, PBC mode, time selection, and output precision. A molecule-whole or centered view is often useful for visualization, but may be unsuitable for diffusion, transport, density, or displacement analysis.

Never infer unwrapped coordinates from an already centered/wrapped trajectory without the required image/history information. Validate atom/site ordering after any subset selection.

### Observable readiness

- Capture interactive selections and exact term names for `gmx energy`.
- Use the `spatial-density-profile` recipe for a one-dimensional `gmx density` profile. Declare axis, groups, density kind, slices, time window, centering/PBC preprocessing and symmetry. For total NPT density, follow the official direction to use `gmx energy` instead.
- Bind RMSD fit and measurement groups separately.
- For RDF, record reference/selection expressions, normalization, exclusion behavior, cutoff, PBC, and bin width.
- For MSD/diffusion, establish an appropriate diffusive regime, dimensionality, PBC/unwrapping route, fit interval, finite-size treatment, and uncertainty.
- Separate equilibration diagnostics from production samples; never optimize discard after seeing the target result without a new protocol record.

Report autocorrelation, effective sample size, block/window sensitivity, replica/seed coverage, and uncertainty. Native tool success does not establish stationarity or model validity.

## Performance work

### Official behavior

GROMACS reports performance and cycle accounting in the run log. Relevant metrics include `ns/day`, `hour/ns`, `ms/step`, and size-normalized throughput. The log also exposes PP/PME balance, communication, neighbor search, constraints, output, and GPU launch costs. Automatic resource selection is often useful; the optimum depends on system, hardware, build, MPI/OpenMP layout, PME, constraints, and accelerator support.

### Operational heuristic

1. Freeze a scientifically accepted TPR and output policy before benchmarking.
2. Record executable/build, host class, ranks, threads, affinity, GPUs, offload settings, PME ranks, dynamic load balancing, and filesystem.
3. Benchmark representative steady-state work long enough to exclude startup noise; compare at least repeat measurements when timing noise matters.
4. Compare the same system, time step, algorithms, and output cadence. Do not compare `ns/day` across different scientific work.
5. Inspect cycle accounting before changing layout. Too many ranks, PP/PME imbalance, excess global communication, I/O, or GPU launch overhead need different responses.
6. Treat any `tune_pme`-modified TPR or changed MDP/output cadence as a new input identity and re-run the relevant correctness checks.
7. Recheck energies, constraints, completion, and target observables after adopting a faster layout. Floating-point trajectories may diverge while ensemble claims remain separately assessable.

Do not encode a universal rank/thread/GPU recipe. Performance advice is build- and machine-specific, and must never weaken the scientific acceptance criteria.

## Minimum handoff

Report at least:

- exact GROMACS version/build and command surface, or `native-not-run`;
- source structure and preparation transformations;
- topology/force-field/water/ion/custom-parameter closure and license state;
- per-phase MDP, TPR, checkpoint, parent, log, energy, trajectory, and final-coordinate hashes;
- every warning/error disposition and unresolved issue;
- completion, minimization/equilibration, sampling, numerical stability, model validity, and scientific acceptance as separate gates;
- performance metrics only with the full resource and protocol context;
- raw versus transformed trajectory inventory and analysis selections;
- current development ceiling: `no_positive_claim`.
