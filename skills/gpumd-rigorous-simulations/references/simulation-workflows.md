# GPUMD v5.3 simulation workflows

Use this guide to design and review ordinary GPUMD molecular-dynamics work. It
does not expand the deterministic guard beyond its synthetic NVE/LJ slice and
does not authorize execution.

## Contents

- [Evidence labels](#evidence-labels)
- [Close the input identity](#close-the-input-identity)
- [Build a staged MD protocol](#build-a-staged-md-protocol)
- [Choose an ensemble and integrator](#choose-an-ensemble-and-integrator)
- [Control output and continuation](#control-output-and-continuation)
- [Benchmark without changing the science](#benchmark-without-changing-the-science)
- [Triage failures](#triage-failures)
- [Accept or stop](#accept-or-stop)

## Evidence labels

- **Official v5.3 fact** means the statement is present in the source or bundled
  documentation at tag `v5.3`, commit
  `f2b46c5d528e985a5bf68becd442b18c0e04396c`.
- **Operational heuristic** means a useful practice, not a GPUMD default or a
  scientific acceptance rule. Predeclare it and validate it for the project.
- **Guard coverage** means the local deterministic parser implements the fact.
  The current guard covers only standard NVE, one LJ format, selected outputs,
  and synthetic fixtures. Everything else remains design-only.

Rolling `gpumd.org` pages may describe a newer development state. Resolve an
exact release first; do not silently mix those pages with v5.3 inputs.

## Close the input identity

### Working-directory contract

Official v5.3 facts:

- `gpumd` is launched without an input-file argument from a directory that
  contains fixed-name `run.in` and `model.xyz` files.
- `run.in` is a sequential command protocol. Blank lines and `#` comments are
  ignored; an invalid command causes startup termination.
- Set the interaction using `potential <potential_filename>` before simulation
  actions. The official command accepts a relative or absolute path, while the
  guard intentionally requires a safe basename in its supported slice.

Before any run, bind the exact hashes of `run.in`, `model.xyz`, every potential
or auxiliary file, the executable, and any parent state. A filename or model
title is not an identity.

### `model.xyz`

Official v5.3 facts:

- Use extended XYZ with mandatory `Lattice`, `species:S:1`, and `pos:R:3`.
- `pbc` defaults to `T T T`; state it explicitly in rigorous work.
- Optional fields include `mass`, `charge`, `vel`, and integer group labels.
- Length and position use Å, velocity Å/fs, mass amu, and charge elementary
  charge.
- Non-NEP potentials use the minimum-image convention; each periodic cell
  thickness must exceed twice the potential cutoff. NEP handles additional
  periodic images internally, but that does not remove finite-size testing.

Check finite coordinates, a nonsingular cell, intended composition and species
order, boundary compatibility, overlaps/short contacts, net momentum policy,
and the mapping between structure species and potential species. Treat a
potential file, training data, and the engine as separately licensed artifacts.

### Potential selection

The v5.3 `potential` overview lists Tersoff variants, EAM, force-constant, LJ,
NEP, hybrid NEP+ILP/SW+ILP/Tersoff+ILP, and a Deep Potential interface. Each
family has its own file grammar, units, species mapping, cutoff behavior, and
possibly build/runtime dependencies. Do not translate a parameter file from
another engine merely because the model family has the same name. The current
guard parses only its documented LJ fixture; every other family needs its exact
v5.3 page, lawful fixture, parser, and tests before a deterministic pass.

For any potential, validate both the interface and the physics: exact bytes and
rights, model/version compatibility, species order, cutoff/periodic-image
conditions, reference structures, short-range behavior, relevant energies,
forces and virials, and the final observable/domain. A file that loads has
passed only an interface gate.

## Build a staged MD protocol

Use separate, named phases and declare the observable produced by each phase:

1. validate structure and potential identity;
2. optionally relax the starting configuration using a version-matched
   supported minimizer;
3. initialize or inherit velocities;
4. equilibrate the intended state;
5. run production with a frozen analysis plan;
6. analyze technical completion, numerical stability, sampling, and the target
   observable as separate gates.

Official v5.3 velocity facts:

- `velocity <temperature> [seed <integer>]` uses K.
- An explicit `vel` field in `model.xyz` takes precedence over the requested
  initial temperature.
- Without either velocities or a `velocity` command, GPUMD uses 300 K.
- Generated velocities have zero total linear and angular momentum, but are not
  initially Maxwell distributed; thermalization is expected during MD.

For reproducibility, never rely on the implicit 300 K or an omitted random
seed. Record whether velocities were generated, supplied, or inherited.

Official v5.3 time-step facts:

- `time_step <dt_fs>` uses fs and propagates to later `run` blocks.
- An optional second value caps the distance any atom may travel in one step in
  Å.
- The documented default is 1 fs, but a default is not evidence of adequacy.

Operational heuristic: perform a time-step sensitivity study using comparable
initial states. Check NVE energy drift, constraint/integration stability, the
fastest relevant motion, and the target observable. Choose the largest step
that meets the predeclared scientific bounds, not the largest step that merely
finishes.

### Run-block semantics

Treat commands from one `ensemble` through the following `run` as one block.
Official v5.3 requires exactly one `ensemble` per `run`. `time_step` propagates,
whereas `ensemble`, `dump_thermo`, `dump_restart`, `dump_xyz`, and analysis
commands such as `compute_hac`/`compute_hnemd` do not. Repeat every intended
non-propagating control in every block.

Operational heuristic: make equilibration and production distinct blocks or
case segments. Predeclare discard windows and output cadence before seeing the
desired result. Run a short, bounded smoke segment before a costly production
segment, but never use the smoke result as production evidence.

## Choose an ensemble and integrator

The v5.3 manual documents these conventional choices:

- `nve`: microcanonical integration without extra parameters;
- `nvt_ber`, `nvt_nhc`, `nvt_bdp`, `nvt_lan`, `nvt_bao`: conventional
  temperature-control families;
- `npt_ber` and `npt_scr`: pressure-control families with cell/boundary-specific
  restrictions;
- separate MTTK, thermal-transport, PIMD, and shock integrators.

For conventional temperature/pressure controls, the manual defines coupling
inputs as relaxation time divided by the integration step. It requires values
at least 1 and gives approximately 100 for temperature coupling and 1000 for
pressure coupling as good choices. These are official suggestions, not
project-specific convergence proof.

For `npt_ber`, distinguish isotropic, orthorhombic, and triclinic control. The
official restrictions include orthogonal boxes for isotropic/orthorhombic
forms and full periodicity for isotropic and triclinic forms. Pressure and
elastic-modulus inputs use GPa. Verify the exact command against the pinned
manual before drafting it; the deterministic guard does not parse NVT/NPT.

Acceptance requires more than target averages. Check the sampled distribution,
thermostat/barostat relaxation relative to physical timescales, cell behavior,
conserved quantities appropriate to the ensemble, and sensitivity of the
target observable.

## Control output and continuation

### Thermodynamics and trajectory

`dump_thermo <interval>` is non-propagating and writes `thermo.out`. The v5.3
format has 18 columns: temperature; kinetic and potential energy; six pressure
components; and nine cell-vector components. Units are K, eV, GPa, and Å.

`dump_xyz <grouping_method> <group_id> <interval> <filename> [properties...]`
writes extended XYZ and always includes wrapped positions. Optional properties
include mass, velocity, force, potential, virial, charge, Born effective
charge, group, and unwrapped position. A negative grouping method selects the
whole system. The command is non-propagating, may occur more than once per run,
and appends to its output file.

Choose cadence from the shortest correlation/event timescale needed by the
analysis and the storage budget. A sparse trajectory cannot later recover lost
dynamics; an unnecessarily dense trajectory can make I/O the bottleneck.

### State-file continuation

`dump_restart <interval>` is non-propagating and overwrites `restart.xyz`. The
file uses the `model.xyz` format and can be copied or renamed to `model.xyz` for
a later run.

That is state-file continuation, not proof of bitwise trajectory continuity.
Before reuse:

1. preserve and hash the parent `restart.xyz` before another update;
2. record the parent segment, final accepted step/time, build, potential, and
   state hash;
3. inspect the state fields actually present and re-audit the child input;
4. repeat all non-propagating controls;
5. keep outputs per segment or bind append byte/row boundaries;
6. do not claim thermostat/barostat internal-state continuity unless the exact
   implementation proves it.

NEP training uses a different `nep.restart` file; see
[nep-model-workflow.md](nep-model-workflow.md).

## Benchmark without changing the science

Official v5.3 describes GPU execution and a normal build that creates `gpumd`
and `nep`. It does not document an MPI launcher for the ordinary executable.
Do not infer multi-GPU execution, arbitrary CLI flags, or performance from the
package name.

Operational heuristic: benchmark a scientifically representative but bounded
case. Keep atom count, potential/model, precision-affecting build flags, GPU
backend, integration step, neighbor conditions, analysis commands, and output
cadence identical. Record warm-up policy, completed steps, wall time, steps/s,
peak memory, and I/O volume. Repeat enough times to expose run-to-run variance.

Never speed up a campaign by silently reducing model fidelity, cell size,
equilibration, production length, replicas, output needed for acceptance, or
convergence thresholds. A faster run with a different scientific contract is
not a performance comparison.

## Triage failures

Classify the first failing gate before changing inputs:

| Symptom | Check first | Do not conclude |
|---|---|---|
| startup termination | exact v5.3 keyword, file presence, species/potential mapping | that a similar keyword from rolling docs is accepted |
| GPU/runtime failure | executable hash, backend, driver/runtime, architecture, memory | that the scientific input is wrong |
| NaN or explosive motion | overlaps, potential domain, units, time step, temperature/pressure control | that a smaller time step alone validates the model |
| NVE drift | time-step sweep, conserved-energy definition, initial state, precision/build | that technical completion implies stable integration |
| temperature/cell runaway | ensemble parameters, units, boundary/cell restrictions, equilibration | that target averages were sampled |
| missing or duplicated rows | run-block cadence, append contamination, interruption, segment accounting | that the final marker proves complete output |
| restart discontinuity | parent hash, fields retained, child controls, append boundaries | exact continuation |
| poor throughput | output cadence, model cost, neighbor density, GPU occupancy/memory | that scientific controls should be weakened |

Preserve the failing artifact and hashes. Change one declared factor at a time,
create a new case/segment identity, and never overwrite the evidence that
motivated the change.

## Accept or stop

Require all applicable gates:

- version/build/GPU identity and lawful artifact use;
- input grammar plus structure/potential compatibility;
- successful process/scheduler state and coherent completion markers;
- complete, finite, uncontaminated requested outputs;
- integration and ensemble-specific numerical behavior;
- equilibration, effective samples, uncertainty, and independent replicas;
- finite-size/cutoff, initial-state, and model-domain sensitivity;
- target-observable validation and expert scientific review.

The current guard can establish only a subset of the first four gates for its
synthetic NVE/LJ profile. See the exact v5.3
[`run.in` overview](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/input_files/run_in.rst),
[`model.xyz` format](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/input_files/model_xyz.rst),
[`potential`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/input_parameters/potential.rst),
[`ensemble` documentation](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/input_parameters/ensemble.rst),
[`velocity`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/input_parameters/velocity.rst),
[`time_step`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/input_parameters/time_step.rst),
[`dump_xyz`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/input_parameters/dump_xyz.rst),
[`thermo.out`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/output_files/thermo_out.rst),
and [`restart.xyz`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/output_files/restart_xyz.rst).
