# LAMMPS 4Jul2026 operational planning and audit guide

Use this guide to design and review LAMMPS input before any provider execution. It is version-bound to the 4Jul2026 release and does not attest that a native LAMMPS executable or real simulation has run in this repository.

## Contents

- [Evidence labels and official sources](#evidence-labels-and-official-sources)
- [Input-script order](#input-script-order)
- [Units, atom data, boundaries, and force fields](#units-atom-data-boundaries-and-force-fields)
- [Neighbors and communication](#neighbors-and-communication)
- [Fixes, integration, and ensembles](#fixes-integration-and-ensembles)
- [Thermo, dumps, and completion](#thermo-dumps-and-completion)
- [Restart and segment lineage](#restart-and-segment-lineage)
- [Replicas and partitions](#replicas-and-partitions)
- [Accelerators and performance](#accelerators-and-performance)
- [Failure triage](#failure-triage)
- [Trajectory and analysis checks](#trajectory-and-analysis-checks)
- [Minimum handoff](#minimum-handoff)

## Evidence labels and official sources

Keep the following labels explicit:

- **Official behavior**: a fact summarized from the LAMMPS 4Jul2026 release documentation linked below.
- **Operational heuristic**: a practical investigation order, not an official default, universal performance rule, or scientific threshold.
- **Project decision**: a unit system, force field, ensemble, parameter, seed, duration, tolerance, or acceptance rule justified by the project.
- **Observed evidence**: captured output from an explicitly authorized provider run. No native run evidence is bundled here.

Primary sources, checked as reachable on 2026-07-22:

- [Input script structure](https://docs.lammps.org/Commands_structure.html)
- [`units`](https://docs.lammps.org/units.html), [`atom_style`](https://docs.lammps.org/atom_style.html), [`boundary`](https://docs.lammps.org/boundary.html), and [`read_data`](https://docs.lammps.org/read_data.html)
- [`pair_style`](https://docs.lammps.org/pair_style.html), [`pair_coeff`](https://docs.lammps.org/pair_coeff.html), and [`special_bonds`](https://docs.lammps.org/special_bonds.html)
- [`neighbor`](https://docs.lammps.org/neighbor.html), [`neigh_modify`](https://docs.lammps.org/neigh_modify.html), and [`comm_modify`](https://docs.lammps.org/comm_modify.html)
- [Thermostats](https://docs.lammps.org/Howto_thermostat.html), [`fix`](https://docs.lammps.org/fix.html), and [`run`](https://docs.lammps.org/run.html)
- [`thermo_style`](https://docs.lammps.org/thermo_style.html), [`thermo_modify`](https://docs.lammps.org/thermo_modify.html), and [run output](https://docs.lammps.org/Run_output.html)
- [`restart`](https://docs.lammps.org/restart.html), [`write_restart`](https://docs.lammps.org/write_restart.html), [`read_restart`](https://docs.lammps.org/read_restart.html), and [restart how-to](https://docs.lammps.org/Howto_restart.html)
- [Multi-replica simulations](https://docs.lammps.org/Howto_replica.html) and [command-line partitions](https://docs.lammps.org/Run_options.html)
- [Accelerator packages](https://docs.lammps.org/Speed_packages.html) and [performance guidance](https://docs.lammps.org/Speed.html)
- [Errors and warnings details](https://docs.lammps.org/Errors_details.html)

Resolve exact command syntax through [official-command-catalog.json](official-command-catalog.json) and [task-recipes.json](task-recipes.json). The guide below explains audit decisions; it is not permission to run LAMMPS.

## Input-script order

### Official behavior

A typical input contains initialization, system definition, simulation settings, and run commands. The last two parts may repeat. `units`, `dimension`, `boundary`, and `atom_style` are initialization choices that normally precede creation of the simulation box. `read_data`, `read_restart`, or `create_box` defines that box and locks several settings.

### Operational audit

Review the complete input and every include as executable code. Expand only literal, local includes for an offline audit. Treat variables, loops, `jump`, `if`, `shell`, Python, plugins, downloads, and run-time command generation as separate code and side-effect surfaces.

Inventory the script in this order:

1. exact release/build, packages, styles, suffixes, and launch options;
2. `units`, `dimension`, `boundary`, `atom_style`, Newton/processor choices;
3. box creation or imported data/restart identity;
4. groups, masses, type/element mapping, charges, molecule/topology attributes;
5. force-field styles, coefficients, external model files, exclusions, and long-range solver;
6. neighbor/communication settings;
7. velocity or parent-state lineage;
8. integration, thermostat, barostat, constraints, restraints, and other fixes;
9. thermo, computes, dumps, restart cadence, and variables used in output;
10. minimization/run segments, stop conditions, and analysis.

Stop when a command appears in the wrong pre-box/post-box phase, a style is absent from the exact binary, or expansion prevents a complete input closure.

## Units, atom data, boundaries, and force fields

### Units

**Official behavior:** `units` selects the units of input parameters, data, coefficients, defaults, and output. Changing unit style requires converting every dimensional input consistently. Potential files with a `UNITS:` tag can be checked by LAMMPS; files without that metadata transfer the verification burden to the user.

**Operational audit:** record a semantic unit map for coordinates, velocity, mass, charge, energy, force, pressure, time, temperature, and every coefficient. Do not label reduced `lj` quantities as SI or laboratory units without an explicit parameterized conversion. A familiar potential filename or element symbol does not prove units.

### Atom style and data file

**Official behavior:** `atom_style` selects the per-atom attributes stored, communicated, and expected in data/restart records. The `Atoms` section format in a data file must match the chosen atom style. `read_data` reads header counts, type counts, box bounds, and named sections.

**Operational audit:** verify:

- the required title/comment line and exact header/section boundaries;
- atom, bond, angle, dihedral, improper, and type counts;
- unique atom IDs, molecule IDs where applicable, and consecutive/allowed type IDs;
- `Atoms # <style>` semantics, image flags, charges, masses, and molecule topology;
- orthogonal, restricted triclinic, or general triclinic box convention;
- coefficient sections versus commands in the input and the precedence intended by the model;
- post-read atom/type counts printed by the exact run.

Do not repair an `Unknown identifier` or `Incorrect format` error by deleting a line until the expected section length and atom-style grammar are established.

### Boundaries and box

Audit each axis as periodic, fixed nonperiodic, shrink-wrapped, or shrink-wrapped with a minimum. Record whether atoms may physically leave, how surfaces/walls are represented, how electrostatics treats nonperiodic dimensions, and whether box deformation is expected.

Operational heuristic: a large initial gap with shrink-wrap boundaries can cause a sudden box change and lost atoms. Diagnose geometry and intended open-boundary behavior before changing communication or lost-atom policy.

### Force-field closure

Treat the following as one provenance closure:

- pair, bond, angle, dihedral, improper, KSpace, and many-body styles;
- all coefficients, mixing rules, cutoffs, shifts/tails, exclusions, and `special_bonds` weights;
- atom-type-to-element order and charge assignment;
- potential/model files, hashes, version/training/domain, source, and license;
- package/style requirements, precision, and accelerator suffix;
- any hybrid/overlay routing and which type pairs each sub-style owns.

An available style is not evidence that its parameterization is valid. For many-body and ML potentials, verify element mapping, supported species, units, neighbor cutoff/domain, and model-specific restrictions from that style's exact manual.

## Neighbors and communication

### Official behavior

The neighbor cutoff is the force cutoff plus the `neighbor` skin. `bin`, `nsq`, and `multi` are different construction strategies. `neigh_modify` controls when lists may rebuild and their storage. With checking enabled, atom migration and periodic remapping occur on rebuild steps. The release defaults are conservative; rebuilding too infrequently can omit interactions and produce incorrect results.

Neighbor-list rebuilding changes floating-point summation order, so restart output or a changed rebuild schedule can alter the exact trajectory. This does not waive the need to test scientific equivalence.

### Operational audit

Record `neighbor` style/skin, `neigh_modify` delay/every/check/once, `one`/`page`, exclusions, binsize or collections, atom sorting, `comm_modify`, Newton settings, and every pair cutoff.

Use this investigation order:

1. Validate geometry, density, units, box size, pair cutoffs, and overlap.
2. Check the neighbor summary, maximum/average neighbors, rebuild count, and dangerous builds.
3. Verify that the communication cutoff covers bonded/topological spans and fix requirements.
4. Test time-step and rebuild sensitivity before relaxing the conservative settings.
5. Increase `one`/`page` only when a physically justified neighbor count exceeds storage; keep page sizing consistent with the official constraint.

Do not use a larger communication cutoff to hide a molecule that is physically blowing apart. Do not use a larger neighbor capacity to hide an accidental high-density or huge-cutoff system.

## Fixes, integration, and ensembles

### Integrator ownership

**Official behavior:** integration fixes update positions and/or velocities. `fix nve`, `fix nvt`, and `fix npt` integrate their groups; not every thermostat fix integrates. For example, a stochastic thermostat may require a separate integration fix.

**Operational audit:** build an atom-group ownership table for every fix. Require exactly one intended time integrator per mobile atom. Check overlaps among groups, rigid bodies, SHAKE/RATTLE constraints, frozen atoms, walls, deformation, external fields, and momentum removal.

Block both `No fixes with time integration` and `One or more atoms are time integrated more than once`. Do not resolve the second by arbitrarily deleting a fix; determine which fix owns integration and which only modifies forces or velocities.

### Time step and initialization

Record unit-style default versus explicit `timestep`, velocity source, temperature distribution, momentum/rotation removal, seed, and restart parent. A seed identifies a pseudo-random stream setup, not independent sampling by itself.

Operational heuristic: minimize and introduce temperature/pressure control in staged segments for an imported or high-energy configuration. A temporary limited/adaptive integration technique is a diagnostic or preparation protocol that requires its own lineage; it must not silently become production dynamics.

### Thermostat and barostat

Record fix style, group, target schedule, damping parameters in the selected unit style, temperature compute/bias, pressure components, coupling mode, drag/chain options, and whether the method supports the claimed ensemble or dynamical observable.

Do not assume `fix langevin` or another thermostat advances coordinates. Do not assume `fix nvt` plus a second `fix nve` is required; `fix nvt` already integrates. Audit the exact style manual.

Separate equilibration from production. A stable temperature/pressure trace alone does not establish the target ensemble, stationarity, effective sample size, or model validity.

## Thermo, dumps, and completion

### Plan output before launch

Use `thermo_style custom` or an equally explicit schema so that the log exposes the planned step/time, temperature, potential/kinetic/total energy, pressure/volume as applicable, and claim-specific observables. Record `thermo` cadence and all `thermo_modify` changes.

Keep `thermo_modify lost error` unless the physical protocol explicitly removes atoms through a nonperiodic boundary or deletion process and separately accounts for them. `lost ignore` is not a general stability fix.

For custom dumps, record style, columns, sort policy, coordinate variant (`x`, `xs`, `xu`, etc.), image flags, box representation, boundary flags, units, cadence, compression, and selection group. A `.lammpstrj` extension does not prove any particular columns.

### Completion gate

Require the exact release banner, intended thermo table(s), planned final step, one matching `Loop time` record for the segment, expected artifacts, and no adverse marker. Also inspect neighbor statistics, atom count, warning context, and timer breakdown.

A `Loop time` line proves that one run/minimize segment reached its reporting point. It does not prove equilibrium, convergence, correct units, a valid force field, a complete multi-segment script, or scientific acceptance.

## Restart and segment lineage

### Official behavior

LAMMPS supports continuation in the same script, binary restart files, or text data exported from a restart. Binary restarts preserve system state and some style/fix state, but do not store every command-defined object. A new script must recreate required fixes, computes, output, variables, groups/regions, and model settings not retained by the relevant styles.

Binary restart files are intended for the same executable and platform, not as a backward/forward/cross-platform archive. Processor count, decomposition, Newton settings, certain stochastic or constraint fixes, velocity-dependent pair styles, and neighbor ordering can prevent an exact trajectory even when continuation is statistically valid. `write_data` is more portable but does not preserve all dynamic algorithm state.

### Operational audit

For every restart, record:

- producing banner, executable/build hash, platform, MPI/rank/thread/GPU layout;
- parent input closure, step, binary restart hash, external model hashes, and warning state;
- `-restart2info` inventory from the producing/matching executable when authorized;
- commands and state restored versus commands explicitly recreated;
- new segment first/last step, `reset_timestep` policy, dump/thermo/restart filenames;
- exact-continuation claim versus statistical-continuation claim and the known blockers.

Use a wildcard restart only after resolving which concrete file it selects and hashing that file. Keep periodic restart sets and the final `write_restart` distinct. A restart write forces neighbor rebuilding and can alter exact floating-point trajectory order; include cadence in the protocol identity when exact comparison matters.

When converting a restart to data, preserve the binary parent and conversion transcript. Treat the converted data as a new-state representation, not as an exact algorithm-state continuation.

## Replicas and partitions

### Official behavior

Multi-replica methods run multiple LAMMPS partitions (MPI worlds) and use method-specific commands such as `temper`, NEB, PRD, TAD, or related variants. Command-line `-partition` determines world layout; partition-specific screen/log naming prevents output collision. The executable and packages must support the selected method.

### Operational audit

Record partition count and processors per partition, replica-to-parameter mapping, per-replica seed and initial state, exchange/communication cadence, shared versus independent files, restart coverage, and scheduler rank mapping. Require unique output directories or unambiguous partition-expanded names.

Do not call exchanging replicas independent samples. Analyze correlation and exchange history according to the estimator. For independent replicas, prove distinct initialization/seed lineage and report between-replica variation.

Operational heuristic: use non-buffered output only for bounded debugging when a crashing multi-replica run may lose the final error message. Record the changed launch option; do not treat it as a scientific fix.

## Accelerators and performance

### Official behavior

LAMMPS offers GPU, INTEL, KOKKOS, OPENMP, and OPT accelerator packages. Accelerated styles are selected through suffixed style names, `suffix`/`-sf`, and package configuration through `package`/`-pk` where applicable. Availability depends on the exact build and hardware; `-help` and `info` expose installed packages/styles.

### Operational heuristic

1. Establish a correct baseline on an immutable input before performance tuning.
2. Record the exact executable, compiler, MPI, packages, precision, suffix/package options, ranks, threads, affinity, accelerators, and driver/runtime.
3. Benchmark a representative steady-state segment with identical physics, atom count, time step, neighbor settings, and output cadence.
4. Inspect loop timing, CPU use, neighbor statistics, communication, pair/KSpace costs, load balance, and memory before changing layout.
5. Compare energies/forces for a bounded diagnostic and reapply completion, stability, ensemble, and observable gates after adopting an accelerated style.
6. Report throughput only with problem size and full resource context. Do not infer a universal best package from another system or machine.

Accelerated precision and reduction order can change exact trajectories. Faster completion is not evidence of model equivalence; validate the intended physical/statistical claim.

## Failure triage

Preserve the full input closure, data/model files, screen/log, exact banner, launch line, and last valid frame before investigating. The table gives an investigation order, not automatic repairs.

| Symptom | Likely branches to distinguish | Blocked shortcut | Operational next evidence |
|---|---|---|---|
| lost atoms | overlap/high force, wrong units, large time step, rapid box change, infrequent neighbor migration, deliberate outflow | `thermo_modify lost ignore` for a closed system | inspect earliest loss, coordinates/energy, box, atom count, neighbor cadence, and serial/small-system reproduction |
| NaN/Inf or non-numeric coordinates/pressure/box | overlapping atoms, invalid geometry/parameters, unit mismatch, excessive time step, aggressive barostat, precision overflow | continuing after the first non-finite value | find the first non-finite step and isolate geometry, units, force-field, integration, and coupling causes |
| bond/angle/SHAKE atoms missing | molecule blew apart or communication cutoff is too short for a valid topology span | blindly increasing `comm_modify cutoff` | compare bond extent, force/temperature trace, pair cutoff+skin, ghost coverage, and topology |
| out-of-range atoms in PPPM/MSM | fast atoms, neighbor skin/update, unstable startup, decomposition | only increasing mesh/communication | check close contacts, time step, neighbor settings, rank sensitivity, and initial equilibration |
| neighbor list overflow | genuine high coordination, long cutoff, dense/overlapped system, wrong units/box | only increasing `neigh_modify one` | inspect density/cutoff/neighbor summary; then size `one` and `page` only if the model requires it |
| too many bins or box much smaller than cutoff | extreme box/cutoff scale, sparse huge domain, unit error | switching neighbor style without diagnosis | verify box and cutoff units, then assess binsize/hash/nsq/multi choices against the exact system |
| unknown/unrecognized style | package not built, suffix requested but unavailable, spelling/version mismatch | replacing with a similarly named style | use exact `-help`/`info`, build manifest, and release manual |
| no integration or double integration warning | missing integrator or overlapping fix groups | suppressing the warning | construct per-group integrator ownership and inspect every fix style |
| incorrect/unknown data section | atom-style mismatch, wrong header counts, missing title/comment, malformed section | deleting the reported row | validate the complete data grammar and section counts |
| segmentation fault or silent MPI abort | unstable settings, memory exhaustion, accelerator/MPI/build defect, buffered error | assuming it is a LAMMPS core bug | reproduce with a small case, non-buffered output when authorized, serial/rank variants, and exact debug build |

An error that appears sooner in parallel can expose a real instability or communication defect; it does not prove the serial run is correct. Conversely, a crash isolated to one accelerator/build is environment evidence, not automatic scientific invalidation of all model settings.

## Trajectory and analysis checks

For each dump segment, verify:

- exact timesteps and expected cadence;
- constant or intentionally changing atom counts;
- unique IDs, type/element mapping, and stable site identity;
- box representation and boundary flags;
- coordinate semantics and image flags sufficient for the intended unwrap;
- finite positions/velocities/forces and no frame truncation;
- restart overlaps, gaps, ID remapping, sort changes, and topology changes.

Preserve raw dumps before conversion. Do not infer unwrapped paths from wrapped coordinates without image/history evidence. A `rerun` command recomputes selected quantities from snapshots under the current force-field/input settings; it does not recreate the original integration trajectory and requires the same topology/type/unit/box semantics.

For RDF, MSD, VACF, transport, stress, or time correlation, predeclare group/type selection, normalization, dimensions, sampling cadence, fit/integration interval, PBC treatment, equilibration discard, effective-sample/uncertainty method, and finite-size correction where applicable. Maintain stateful compute IDs across restarts only when the exact manual says the underlying reference state can continue.

## Minimum handoff

Report at least:

- exact release banner, executable/build hash, packages/styles/suffixes, or `native-not-run`;
- input/include/data/model closure and unit/type/element/license maps;
- boundaries, box, neighbor/communication, force field, fixes, integrator ownership, ensemble, seeds, and time step;
- per-segment parent, restart, input, log, dump, thermo, and final-state hashes;
- every warning/error disposition and unresolved unsupported surface;
- completion, numerical stability, equilibration, sampling, model validity, analysis validity, and scientific acceptance as separate gates;
- replica/partition lineage and performance context when used;
- raw versus converted/rerun trajectory inventory;
- current development ceiling: `no_positive_claim`.
