# VASPKIT environment, installation, and license boundary

## Current repository evidence

On 2026-07-18, `command -v vaspkit` returned no executable on the maintainer
machine. No VASPKIT banner, help text, interactive menu, calculation output, or
official example was processed by a native binary. Current catalog and recipes
are official-documentation-grounded and `native-not-run`.

The Python catalog and narrow band guard require Python 3.10+ and the standard
library only. They never download or launch VASPKIT.

## What a user must install

The official installation page distributes compiled VASPKIT binaries for
Windows, macOS, and Linux and links the release archive on SourceForge. Choose a
package that matches the actual operating system and architecture. Current
official archive evidence in this candidate includes VASPKIT 1.5.1 for Linux
x86_64 and VASPKIT 1.5.0 for Linux x86_64 and macOS Intel. A macOS Intel binary
is not automatically a native Apple Silicon binary, and a Linux executable
cannot serve as macOS execution evidence.

After obtaining the package from the official release route and reviewing its
current terms:

1. unpack it outside this Git repository;
2. add its `bin` directory to `PATH` or supply an explicit executable path;
3. create/configure `~/.vaspkit` from the package template;
4. install the optional plotting stack needed by the chosen tasks;
5. keep VASP potential libraries and all licensed `POTCAR` data outside Git.

The official 1.5 installation page lists at least:

- Python 3.5 or newer;
- NumPy 1.15.4 or newer;
- SciPy 1.1.0 or newer;
- Matplotlib 3.0.1 or newer.

Those are vendor-documented minimums, not this repository's tested compatibility
matrix. Record the actual versions and test the selected task.

## `~/.vaspkit` configuration

The official guide shows these behavior-changing settings:

| Key | Required review |
|---|---|
| `VASP5` | Match the VASP file convention. |
| `LDA_PATH`, `PBE_PATH`, `GGA_PATH` | Point to the user's lawful local potential sets; never record real private paths in fixtures. |
| `POTCAR_TYPE`, `GW_POTCAR`, `RECOMMENDED_POTCAR` | Confirm the intended functional/potential family and exact element order. |
| `SET_FERMI_ENERGY_ZERO` | Record whether band/DOS energies are shifted to the Fermi level. |
| `MINI_INCAR`, `USER_DEFINED_INCAR` | Record which INCAR template source is used. |
| `SET_INCAR_WRITE_MODE` | Inspect overwrite, append, and backup behavior before running in a populated directory. |
| `PYTHON_BIN`, `PLOT_MATPLOTLIB` | Confirm plotting interpreter and packages if automatic figures are requested. |
| `VASPKIT_UTILITIES_PATH`, `ADVANCED_USER` | Treat user utilities as separate code with their own provenance and tests. |

Do not print a full `~/.vaspkit` into logs if it contains private paths. Record
only redacted settings relevant to the task.

## Native preflight record

Before the first task on a machine, collect:

```text
command -v vaspkit
vaspkit -help
uname -sm
```

Also capture:

- exact banner and version;
- executable/package SHA-256;
- official release URL and release date;
- platform, architecture, and runtime compatibility;
- usage-agreement URL and review date;
- relevant redacted `~/.vaspkit` keys;
- Python/NumPy/SciPy/Matplotlib versions if plotting is used.

Run the first menu test in a fresh scratch directory. Task 102 with a public,
non-licensed `POSCAR` is a reasonable smoke-test candidate only after reviewing
the installed help and prompts. Record argv/stdin, stdout, stderr, initial file
inventory, and created/changed files. Do not use a smoke test to claim scientific
convergence.

## License and data handling

The official installation page states a VASPKIT usage agreement, publication
acknowledgment requirement, no-warranty boundary, and that terms may change.
Review the current page at use time; this Skill does not give legal advice or
redistribute the binary.

VASPKIT commonly reads VASP outputs and can assemble `POTCAR`. VASP potentials
and many real calculation trees are licensed, private, or unpublished:

- never commit VASPKIT binaries or `POTCAR` contents;
- never copy a user's potential directory into a fixture;
- never publish raw private VASP outputs merely to test an adapter;
- use public companion examples, synthetic fixtures, or user-authorized
  redacted evidence;
- store executable and input/output hashes rather than restricted bytes when
  provenance is sufficient.

## Execution boundary

The candidate catalog CLI only discovers tasks and renders
documentation-grounded plans. The existing `vaspkit_guard.py` only audits a
narrow synthetic task-211/252 protocol and table layout. Neither tool starts
VASPKIT.

A future native adapter must:

1. require an explicitly supplied executable profile and scratch worktree;
2. reject unresolved placeholders and documentation conflicts;
3. bind exact VASP-parent inputs before launch;
4. capture stdin/argv and output streams;
5. inventory all side effects without overwriting the only calculation copy;
6. hash and parse the expected task output;
7. report native execution separately from scientific acceptance.
