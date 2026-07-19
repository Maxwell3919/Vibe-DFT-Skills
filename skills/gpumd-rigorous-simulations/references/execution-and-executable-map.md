# GPUMD v5.3 execution and executable map

## Evidence and native-validation state

The command shapes below are grounded in the official GPUMD `v5.3` tag at
commit `f2b46c5d528e985a5bf68becd442b18c0e04396c`. The maintainer machine was
macOS arm64 and had no `gpumd`, CUDA, or ROCm tools in `PATH` on 2026-07-19,
so no native GPUMD run was performed there. Keep documented invocation,
offline artifact validation, and native execution as separate claims.

## Build and identify the executable

The v5.3 repository README instructs users to run `make` in `src`; the normal
build creates `src/gpumd` and `src/nep`. The CUDA build requires an NVIDIA GPU,
CUDA, and a compatible C++ toolchain. The exact v5.3 source tree contains
`src/makefile.hip`, and the official installation page documents the AMD
ROCm/HIP build command as `make -f makefile.hip`. Still bind the actual backend,
makefile hash, compiler, flags, and runtime instead of inferring compatibility
from the presence of that file.

Inventory without launching the engine:

```text
command -v gpumd
sha256sum "$(command -v gpumd)"       # GNU/Linux
shasum -a 256 "$(command -v gpumd)"  # macOS inventory only, not execution
```

The v5.3 `gpumd` source does not implement a documented `--version` or `-h`
mode. Running `gpumd --version` is therefore not a safe probe: the program
starts its normal fixed-file workflow. Establish version/build identity from
all of the following:

1. exact source tag/commit and immutable build recipe;
2. executable SHA-256 and compiler/build flags;
3. the `version 5.3` banner in a separately authorized normal run;
4. the GPU backend/runtime evidence captured with that same run.

Useful environment probes are inventory commands, not proof of compatibility:

```text
# NVIDIA route
nvidia-smi --query-gpu=name,compute_cap,driver_version --format=csv,noheader
nvcc --version

# AMD route
rocminfo
hipcc --version
```

Record full outputs or hashes outside this repository. A missing command,
driver/runtime mismatch, unsupported GPU architecture, or banner/build
contradiction blocks execution. Apple Silicon has no official native GPUMD
execution route in the reviewed material.

## Real invocation and working-directory contract

GPUMD reads fixed filenames from the current directory. The official README
uses `path/to/gpumd` from an example directory; it does not pass an input-file
argument. Use one isolated clean case directory containing at least `run.in`,
`model.xyz`, and every potential/data file referenced by `run.in`:

```text
cd <isolated-case-directory>
<absolute-path-to-v5.3-gpumd> > gpumd.stdout 2> gpumd.stderr
```

Do not add MPI launchers or CLI flags unless an exact version/build-specific
official source documents them. Bind scheduler exit state and any launcher or
GPU selection performed outside GPUMD. Never append a retry to an earlier
stdout, `thermo.out`, or trajectory.

Before launch, require:

- a passing offline plan and input audit for the supported task slice;
- exact hashes for `run.in`, `model.xyz`, all potential/model files, and any
  state-file parent;
- executable/build/backend identity and a supported GPU allocation;
- a clean output destination because many GPUMD output files append;
- explicit execution authority, wall-time/resource limits, and stop policy.

## Process and output failure semantics

For the v5.3 normal `gpumd` executable, source inspection establishes the
banner and normal markers used by the guard:

```text
Started running GPUMD.
*                     version 5.3                             *
Finished executing the commands in run.in.
Time used = <seconds> s.
Finished running GPUMD.
```

Accept technical completion only when the process/scheduler exit state is
successful, stderr has no fatal diagnostic, all required markers occur once in
one coherent stdout stream, requested output files have the expected bounded
grammar/cadence, and no non-finite values occur. Any signal, nonzero exit,
driver failure, out-of-memory event, timeout, missing/duplicate marker,
truncated artifact, or unexpected append blocks completion. Normal markers do
not prove equilibration, convergence, model validity, or statistical adequacy.

## Input, output, units, and side effects

The supported offline slice uses:

- `run.in`: command protocol;
- `model.xyz`: extended-XYZ model with cell, boundary, species, positions, and
  optionally mass/velocity/group data;
- one explicitly parsed LJ potential plus independent provenance;
- `thermo.out`: appended 18-column thermodynamic rows;
- a named `dump_xyz` extxyz trajectory;
- `restart.xyz`: overwritten state file created by `dump_restart`.

For MD in the reviewed v5.3 documentation, record mass in amu, charge in `e`,
length in Å, time in fs, energy in eV, pressure in GPa, temperature in K, and
velocity in Å/fs. `thermo.out` contains T, kinetic energy, potential energy,
six pressure components, and nine cell-vector components in that order.
Task-specific keywords can add other units and files; unsupported commands
must not inherit this small-slice parser's claim.

## Restart and segment lineage

`dump_restart <interval>` is non-propagating and updates `restart.xyz` by
overwrite. The v5.3 manual says that `restart.xyz` has the model-file format
and can be renamed or copied to `model.xyz` to restart. Source inspection shows
positions, mass, velocities, boundary, cell, and groups are written.

Treat this as state-file continuation, not bitwise or exact integrator
continuation. Before the child run:

1. preserve and hash the parent `restart.xyz` before it can be overwritten;
2. record parent run ID, final accepted step/time, state hash, executable/build,
   potential closure, and child segment start;
3. re-audit the child `model.xyz` and repeat every non-propagating run control;
4. keep outputs per segment or bind append offsets/hashes explicitly;
5. do not claim thermostat/barostat internal-state continuity unless exact
   version-matched evidence establishes that state.

## Typical acceptance workflow

1. Run `gpumd_guard.py plan` and `audit-input` on immutable candidate inputs.
2. Independently capture executable/source/GPU evidence and authorize one
   bounded launch in a clean directory.
3. Run the no-argument `gpumd` command above; preserve process/scheduler exit,
   stdout, stderr, all outputs, and pre/post inventories.
4. Run `audit-output` and `audit-trajectory` on the exact segment.
5. Separately evaluate time-step/NVE drift, equilibration, effective samples,
   uncertainty, replicas, finite-size/cutoff sensitivity, and potential domain.
6. Bind any restart child to the exact parent state; never merge retries into
   one apparent run.

This development Skill validates a deliberately small synthetic slice. It has
not natively executed GPUMD and cannot authorize execution or a positive
scientific claim.

## Official URLs

- v5.3 tag: <https://github.com/brucefan1983/GPUMD/tree/v5.3>
- v5.3 README/build/run instructions:
  <https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/README.md>
- v5.3 normal executable/banner source:
  <https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/src/main_gpumd/main.cu>
- v5.3 bundled manual:
  <https://github.com/brucefan1983/GPUMD/tree/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc>
- official rolling installation page: <https://gpumd.org/installation.html>
