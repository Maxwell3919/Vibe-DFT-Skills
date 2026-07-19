# Official sources, environment, and licenses

## Parser and planner core

- Runtime: CPython 3.11 or newer, standard library only.
- Network: not required and not used.
- Supported candidate parser inputs: UTF-8 XYZ and the documented local extxyz subset.
- External execution: disabled unless the user supplies the execution flag and every gate passes.
- Candidate license: inherited from the repository; verify it before redistribution.

## Provider profiles

| Profile | Expected identity | License boundary | Candidate behavior |
|---|---|---|---|
| `ovito-basic` | OVITO Basic/Python module 3.15.5 | Mixed MIT and GPL-3.0-only components; obligations and redistribution are component-dependent | metadata probe; exact-version Basic frame-metadata execution only |
| `ovito-pro` | OVITO Pro 3.15.5 | Restricted proprietary EULA; entitlement required; activation material must not be redistributed | planning only; execution always refused |

Package or application presence does not establish edition, entitlement, or permission to
redistribute. Do not infer Pro-only capability from Basic. Treat user trajectories and generated
artifacts under their own data/license attestations.

## Primary official references

- OVITO home and downloads: https://www.ovito.org/
- OVITO Python installation: https://www.ovito.org/docs/current/python/introduction/installation.html
- OVITO file I/O API (`import_file`, `export_file`): https://www.ovito.org/docs/current/python/modules/ovito_io.html
- OVITO pipeline API (`Pipeline.compute`, `FileSource.load`): https://www.ovito.org/docs/current/python/modules/ovito_pipeline.html
- OVITO data API (`DataCollection`, `SimulationCell`, particle properties): https://www.ovito.org/docs/current/python/modules/ovito_data.html
- OVITO modifiers API: https://www.ovito.org/manual/python/modules/ovito_modifiers.html
- OVITO input formats: https://www.ovito.org/docs/current/reference/file_formats/file_formats_input.html
- OVITO output formats: https://www.ovito.org/docs/current/reference/file_formats/file_formats_output.html
- OVITO XYZ/extxyz semantics: https://www.ovito.org/manual/reference/file_formats/input/xyz.html
- OVITO displacement mapping: https://www.ovito.org/docs/current/reference/pipelines/modifiers/displacement_vectors.html
- OVITO licenses: https://www.ovito.org/manual/licenses/index.html

Official API semantics used by this candidate are version-bound: `import_file()` returns a
`Pipeline`; frame indices range from zero to `source.num_frames - 1`; `Pipeline.compute(frame)`
returns an independent `DataCollection`; `sort_particles=False` preserves source storage order;
and displacement mapping relies on Particle Identifier when available, otherwise equal particle
count and storage order are only an assumption. OVITO's XYZ reader treats coordinates as
simulation/source units, and extxyz `Lattice` without `pbc` may be interpreted as fully periodic;
the candidate therefore blocks missing explicit PBC rather than adopting that reader default.

## Version-bound Python and CLI interface

- `ovito.io.import_file(location, **params) -> Pipeline` auto-detects supported local, URL, or
  numbered-sequence sources. This candidate supplies `sort_particles=False`; enabling it would
  reorder by Particle Identifier when available and break source-order evidence.
- `Pipeline.compute(frame=None) -> DataCollection` computes frame zero by default in a
  non-interactive script. Valid frames are `0..pipeline.source.num_frames-1`, and the returned
  snapshot is independent of later pipeline computations.
- `FileSource.load(location, **params)` replaces an existing source. It must therefore be recorded
  as an input-identity change, not treated as an in-place reread of the prior trajectory.
- `ovito.io.export_file(data, file, format, **params)` exports frame zero by default. Multi-frame
  bounds and format-specific particle columns must be explicit; text precision and identifier
  regeneration policies belong in provenance and require an output reparse before acceptance.
- The integrated command shape is `ovitos [-o FILE.ovito] [-g] [SCRIPT.py] [args]`; edition,
  license, interpreter, and environment remain distinct evidence. Neither `ovitos` nor the Python
  distribution was present in the checked environment, so no native command or API was run.

For extxyz, `Lattice` stores row-like vectors `a,b,c` as nine flattened values, whereas OVITO's
3x4 `SimulationCell` exposes the three vectors as matrix columns. The executor performs that
explicit transpose and compares every component. XYZ/extxyz itself does not establish a physical
length unit; OVITO modifiers use the simulation/source unit, not an implicit angstrom contract.

Check exact 3.15.5 documentation before integration. The repository's authority record for OVITO
is still planned, so live official pages are not a frozen version-matched documentation snapshot.

## Platform preparation

The repository provider profile targets Linux x86_64, macOS x86_64/arm64, and Windows x86_64.
Prepare an isolated environment, verify package/application and edition identity, record OS and
architecture, preserve component notices, and keep entitlement receipts outside artifacts.

The current candidate's no-overwrite atomic file publisher additionally requires POSIX-style
`dir_fd` support for `open`, `stat`, `link`, and `unlink`. Linux/macOS are the tested publication
shape. Windows activation remains blocked until an equivalent no-replace publisher and mutation
suite are added; unsupported hosts return `ATOMIC_OUTPUT_UNAVAILABLE` instead of weakening safety.

Rendering may additionally require a supported graphics/headless configuration, fonts, codec,
and deterministic camera/scene settings. None is established by the candidate probe.
