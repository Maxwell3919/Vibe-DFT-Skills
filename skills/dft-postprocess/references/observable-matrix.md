# Observable routing matrix

| Observable | Current route maturity | Required source evidence | Structured output | Critical validation |
|---|---|---|---|---|
| energy/SCF/relax | real-artifact-validated (QE/VASP) | main output plus run settings | JSON summary and CSV trace | completion, electronic/geometry status separation, units, step order |
| bands | real-artifact-validated (QE/VASP) | eigenvalues, k path, labels, Fermi/reference energy | long-form CSV/JSON | band/k dimensions, reference, spin/SOC, path mapping |
| DOS/PDOS | real-artifact-validated (QE/VASP) | energy grid, total/projected channels | CSV/JSON | grid alignment, normalization, channel/site/orbital mapping |
| phonon | real-artifact-validated (QE); VASP design-only | q path/mesh, frequencies, explicit unit | CSV/JSON | q mapping, units, imaginary sign, direct vs interpolated evidence |
| EPC | real-artifact-validated (QE); VASP design-only | alpha2F/lambda, smearing, optional mode/q contributions | CSV/JSON | completeness, smearing alignment, explicit q-weight boundary |
| work function | real-artifact-validated (QE); VASP potential/Fermi combination not yet real-data validated | potential grid, explicit vacuum window, conversion, Fermi level | JSON and window table | source-matched reference, explicit window, no automatic plateau claim |
| charge/ELF/Bader | real-artifact-validated (QE/VASP) | grid or ACF output | tabular/grid summary | grid shape, coordinate scale, charge convention, electron closure |
| NEB | synthetic-validated (generic table) | caller-mapped image coordinates, energies, optional forces | CSV/JSON | image order, endpoints, reference energy; native formats unvalidated |
| optical | synthetic-validated (generic table) | caller-mapped complex dielectric components | CSV/JSON | monotonic eV grid, tensor mapping, broadening declaration; native formats unvalidated |

Unsupported formats or missing dependencies produce `SCRIPT_GAP` or `TOOL_UNAVAILABLE`, not invented results.
