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
| CP2K official repositories | `cp2kparse`, `cp2k_bs2csv`, `cp2k_pdos`, `xyz_restart_cleaner` | structured output, band conversion, PDOS convolution, restart-trajectory cleanup |
| VASP ecosystem | VASPKIT, Bader, critic2, phonopy, sumo, pyprocar, Wannier90 | structured extraction, topology/charge/phonon/band workflows |
| Python | NumPy, SciPy, pandas, Matplotlib, ASE, pymatgen | normalization, validation, numerical analysis, plotting |
| 3D visualization | VESTA CLI | structure plus scalar-field sections/isosurfaces and raster export |

Before invocation, record executable/package path, version command, required inputs, outputs, overwrite behavior, expected units, and safe failure mode. If unavailable, report `TOOL_UNAVAILABLE`; do not auto-install.

## VASPKIT table-adapter boundary

- Prefer native `EIGENVAL`/`KPOINTS`/`POSCAR`/explicit-reference parsing when those files are available. Do not invoke VASPKIT merely to duplicate an already supported native route.
- Accept `BAND.dat` or `REFORMATTED_BAND.dat` plus `KLABELS` only through the table adapter. Require the caller to declare one additive energy offset and describe its reference provenance.
- To correct data already shifted by one reference to another, use `offset = source_reference_ev - target_reference_ev` and retain both source records outside any material-specific script. The adapter performs no directory-name inference.
- Current adapter maturity is `synthetic-validated` because no real VASPKIT table pair was found in the authorized validation roots. Availability of the `vaspkit` executable does not raise table-format maturity by itself.

## ASE structure-view boundary

- Use ASE only as a structure reader and element-display data source; record its package version through capabilities.
- Show one cell plus crystallographically equivalent boundary images. Do not expand a supercell or search for external atoms unless the caller explicitly requests a different structure input.
- Treat covalent-radius or caller-distance connections as graphical connectivity. Keep element colors, sphere radii, distance limits, and view directions configurable and recorded.

CP2K tools remain unimplemented backends until their adapters pass synthetic, format-fixture, real-artifact, and tool-integration validation. `cp2kparse` output can contain host, account and working-directory metadata; never publish its raw JSON. Whitelist normalized values and emit only safe labels plus hashes.

## VESTA CLI adapter boundary

- The current backend route is `design-only`: repository tests exercise internal project rewriting and fail-closed return-code classification, but do not execute the complete public adapter, and no immutable end-to-end executable receipt is registered. Finding or successfully running a local VESTA executable does not activate or promote the route.
- Discover `VESTA`/`vesta` on `PATH` or the standard macOS application-bundle executable; do not auto-install it.
- Convert a grid with `-nogui -i ... -o ...`, then validate the saved project header, density import, and isosurface block before rendering.
- The tested macOS build may return 255 after a successful conversion. Accept that result only when the output project is nonempty and parseable and the log contains `Saved data to:`; all other nonzero results fail closed.
- Rewrite the project density import to the recorded absolute grid path because CLI replay may resolve converter-generated relative paths against the launch directory rather than the project directory.
- Export with `-open ... -export_img ...`, wait for a stable valid PNG, then terminate a renderer that remains open. Record the raw return code and whether termination followed a verified export.
- VESTA uses one project entry for paired positive/negative surfaces and applies its inverse-color convention to the negative surface. Record that policy instead of claiming an independently selected negative RGB value.
- VESTA documents format-specific import behavior. Native VASP charge-density grids may be converted on import, so require the isovalue unit in VESTA-imported terms; do not silently reuse a raw-file threshold.
