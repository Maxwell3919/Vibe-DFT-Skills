# Tool registry and invocation policy

## Selection order

1. Prefer official code outputs and official postprocessing executables for software-defined quantities.
2. Use deterministic Python parsing for documented, stable text/XML formats.
3. Use third-party tools only when their capability, version, input contract, and output provenance are recorded.
4. Do not silently substitute one definition or normalization for another.

## Capability groups

| Group | Candidate tools | Typical roles |
|---|---|---|
| QE official | `bands.x`, `dos.x`, `projwfc.x`, `pp.x`, `average.x`, `q2r.x`, `matdyn.x` | bands, DOS/PDOS, real-space fields, planar averages, phonon interpolation |
| VASP ecosystem | VASPKIT, Bader, critic2, phonopy, sumo, pyprocar, Wannier90 | structured extraction, topology/charge/phonon/band workflows |
| Python | NumPy, SciPy, pandas, Matplotlib, ASE, pymatgen | normalization, validation, numerical analysis, plotting |

Before invocation, record executable/package path, version command, required inputs, outputs, overwrite behavior, expected units, and safe failure mode. If unavailable, report `TOOL_UNAVAILABLE`; do not auto-install.
