# Observable routing matrix

| Observable | Required source evidence | Structured output | Critical validation |
|---|---|---|---|
| energy/SCF/relax | main output plus run settings | JSON summary and CSV trace | completion, units, step order, final value provenance |
| bands | eigenvalues, k path, labels, Fermi/reference energy | long-form CSV/JSON | band/k dimensions, reference, spin/SOC, path mapping |
| DOS/PDOS | energy grid, total/projected channels | CSV/JSON | grid alignment, normalization, channel/site/orbital mapping |
| phonon | q path/mesh, frequencies, interpolation/direct provenance | CSV/JSON | q mapping, units, imaginary sign, direct vs interpolated evidence |
| EPC | k/q meshes, smearing/integration, mode/q contributions | CSV/JSON | completeness, mesh pairing, normalization, convergence boundary |
| work function | planar average, vacuum windows, Fermi level | JSON and window table | energy reference, flatness, both sides, dipole/asymmetry |
| charge/ELF/Bader | grid/structure/tool output | tabular/grid summary | cell/grid alignment, charge convention, tool/version |
| NEB | image mapping, energies, forces | CSV/JSON | image order, endpoints, force convergence, reference energy |

Unsupported formats or missing dependencies produce `SCRIPT_GAP` or `TOOL_UNAVAILABLE`, not invented results.
