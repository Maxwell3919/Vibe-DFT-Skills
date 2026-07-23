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
| `ovito-basic` | internal label for the standalone `ovito` Python distribution 3.15.5, not a package named `ovito-basic` | module distributed under MIT; bundled third-party notices still apply | metadata probe; exact-version frame-metadata execution only |
| `ovito-pro` | OVITO Pro desktop/`ovitos` 3.15.5 | restricted proprietary EULA; entitlement required; activation material must not be redistributed | planning only; execution always refused |

OVITO Basic desktop is a separate MIT-distributed binary surface. The vendor `ovito` conda package
contains the Python module and Pro desktop application; only the desktop requires a paid license.
The conda-forge `ovito` package contains Basic desktop but not the Python module. The standalone
Python module exposes all analysis and rendering APIs, including capabilities marked Pro-only in
the desktop GUI. Package or application presence does not establish edition, entitlement, or
permission to redistribute. Treat user trajectories and generated artifacts under their own
data/license attestations.

## Primary official references

- OVITO home and downloads: https://www.ovito.org/
- OVITO Python installation: https://www.ovito.org/docs/current/python/introduction/installation.html
- OVITO 3.15.5 exact PyPI release and wheel metadata: https://pypi.org/project/ovito/3.15.5/
- OVITO file I/O API (`import_file`, `export_file`): https://www.ovito.org/docs/current/python/modules/ovito_io.html
- OVITO pipeline API (`Pipeline.compute`, `FileSource.load`): https://www.ovito.org/docs/current/python/modules/ovito_pipeline.html
- OVITO data API (`DataCollection`, `SimulationCell`, particle properties): https://www.ovito.org/docs/current/python/modules/ovito_data.html
- OVITO modifiers API: https://www.ovito.org/manual/python/modules/ovito_modifiers.html
- OVITO Python-module scope: https://www.ovito.org/docs/current/python/introduction/introduction.html
- OVITO input formats: https://www.ovito.org/docs/current/reference/file_formats/file_formats_input.html
- OVITO output formats: https://www.ovito.org/docs/current/reference/file_formats/file_formats_output.html
- OVITO XYZ/extxyz semantics: https://www.ovito.org/manual/reference/file_formats/input/xyz.html
- OVITO displacement mapping: https://www.ovito.org/docs/current/reference/pipelines/modifiers/displacement_vectors.html
- OVITO Basic/Pro feature boundary: https://www.ovito.org/manual/ovito_pro.html
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
- Install the standalone module into a regular Python interpreter with `pip install -U ovito`, or
  use the vendor conda channel command pinned in the official installation page. The integrated
  command shape `ovitos [-o FILE.ovito] [-g] [SCRIPT.py] [args]` belongs to OVITO Pro; edition,
  license, interpreter, and environment remain distinct evidence. This content review did not
  install, import, or execute OVITO, so native validation remains `native-not-run`.

For extxyz, `Lattice` is a 3x3 matrix whose vectors are columns, flattened in Fortran column-major
order as `ax ay az bx by bz cx cy cz`. OVITO's 3x4 `SimulationCell` also exposes the three vectors
as matrix columns. The inventory stores `[a,b,c]`; the bounded executor reads those columns into
the same vector list and compares every component. XYZ/extxyz itself does not establish a physical
length unit; OVITO modifiers use the simulation/source unit, not an implicit angstrom contract.

Check exact 3.15.5 documentation before integration. The repository's authority record for OVITO
is still planned, so live official pages are not a frozen version-matched documentation snapshot.

## Platform preparation

The conservative standalone-module profile targets Linux x86_64, macOS arm64, and Windows x86_64
with Python 3.10 through 3.14. Exact 3.15.5 PyPI wheels require macOS 12 or newer; vendor conda
artifacts use a distinct matrix and permit macOS 11 or newer. No exact 3.15.5 macOS x86_64 artifact
was found in either reviewed channel. Prepare an isolated environment, verify the exact artifact,
channel, package/application and edition identity, record OS and architecture, preserve component
notices, and keep entitlement receipts outside artifacts.

The current candidate's no-overwrite atomic file publisher additionally requires POSIX-style
`dir_fd` support for `open`, `stat`, `link`, and `unlink`. Linux/macOS are the tested publication
shape. Windows activation remains blocked until an equivalent no-replace publisher and mutation
suite are added; unsupported hosts return `ATOMIC_OUTPUT_UNAVAILABLE` instead of weakening safety.

Rendering may additionally require a supported graphics/headless configuration, fonts, codec,
and deterministic camera/scene settings. None is established by the candidate probe.
