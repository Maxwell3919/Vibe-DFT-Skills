# Dependencies and capability boundaries

## Validated runtime profile

| Library | Role | Current boundary |
| --- | --- | --- |
| ASE | Materialize the selected CIF block, periodic geometry, neighbor enumeration, element data | Does not resolve correlated occupancy/disorder ensembles. |
| Gemmi 0.7.5+ | Strict CIF 1.1 document parsing and data-block/tag/loop inventory | Gemmi documents that CIF2/DDLm syntax is not supported; CIF2 is routed elsewhere. |
| PyCifRW 5.0.1+ | CIF2 parsing and block/loop access | Dictionary-driven semantic validation is not enabled by the current CLI. |
| NumPy | Cell/vector operations and static projections | Numerical backend only. |
| jsonschema | Draft 2020-12 structure-manifest validation | Structural constraints do not replace crystallographic review. |
| spglib 2.7+ | Symmetry dataset, tolerance sweep, Wyckoff/equivalent sites, standardized cells | Partial/mixed occupancy is not represented by spglib species labels. |
| Matplotlib | Optional static PNG projections | Images are presentation artifacts, not numeric evidence. |

The full development profile is declared in the repository `requirements-dev.txt`. Gemmi can degrade to an ASE CIF1.1 parser if it is unavailable, but the artifact is then `WARN`; PyCifRW is required for CIF2. jsonschema and ASE are required for successful artifact generation. Matplotlib is only needed with `--views-dir`.

Primary references:

- [IUCr CIF 1.1 file syntax](https://www.iucr.org/resources/cif/spec/version1.1/cifsyntax)
- [IUCr CIF 2.0 specification](https://journals.iucr.org/j/issues/2016/01/00/aj5269/)
- [IUCr CIF dictionary browser](https://www.iucr.org/resources/cif/dictionaries/browse)
- [Gemmi CIF documentation](https://gemmi.readthedocs.io/en/latest/cif.html)
- [PyCifRW documentation](https://www.iucr.org/resources/cif/software/pycifrw)
- [ASE CIF I/O](https://wiki.fysik.dtu.dk/ase/ase/io/formatoptions.html#cif)
- [ASE neighbor lists](https://wiki.fysik.dtu.dk/ase/ase/neighborlist.html)
- [spglib Python API](https://spglib.readthedocs.io/en/stable/python-interface.html)

## Optional future adapters

These libraries are not evidence that a feature is implemented. Add an adapter, dependency declaration, fixtures, maturity label, and fail-closed diagnostics before exposing any of them through the CLI.

| Candidate | Suitable module |
| --- | --- |
| pymatgen | Structure matching, oxidation-state helpers, supercell/slab/defect transformations, graph-based local environments, XRD, format export. |
| SciPy | Assignment/KD-tree primitives for structure comparison and geometric clustering. |
| NetworkX | Periodic structure-graph analysis after a validated edge-construction method exists. |
| SeeK-path | Standard reciprocal-space paths after symmetry and cell-standardization evidence is accepted. |
| pymatgen ChemEnv/CrystalNN or equivalent | Alternative coordination definitions; method and parameters must be explicit and must not overwrite distance-shell coordination. |
| DScribe and matminer | Descriptor and dataset features for batch screening; keep outside the core runtime. |
| OPTIMADE clients, mp-api, COD adapters | External discovery/cross-reference modules with network, authentication, license, cache, and provenance controls. |

Magnetic CIF, modulated structures, powder/reflection data, dictionary validation, and database identity resolution each require their own format fixtures and claim boundaries. The current parser only records the core structure subset it understands and retains a tag inventory for future adapters.
