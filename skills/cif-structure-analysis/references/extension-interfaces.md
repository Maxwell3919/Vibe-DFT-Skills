# CIF extension interfaces

## Implemented modules

- `ciftool.document`: syntax routing, data-block selection, raw metadata, uncertainty, occupancy/disorder, and tag inventory.
- `ciftool.neighbors`: periodic-image enumeration, canonical edges, nearest shells, coordination, short-distance flags, and target bond-length matching.
- `ciftool.symmetry`: spglib evidence, declaration comparison, tolerance sweep, and standardized-cell summaries.
- `ciftool.manifest`: safe provenance, structure identity, validation aggregation, element styles, relative artifacts, and schema validation.
- `analyze_cif.py`: the orchestration CLI and Markdown/static-PNG presentation layer.

Keep parsing, scientific analysis, presentation, and external tool execution separate. A new module must return structured payload plus diagnostics; it must not print claims or mutate another module's result silently.

## Reserved modules

| Module | Contract responsibility |
| --- | --- |
| `quality` | Formula/Z/occupancy consistency, duplicate or overlapping sites, cell validity, dictionary-validation adapter. |
| `coordination` | Named distance, covalent-radius, Voronoi, CrystalNN, or ChemEnv methods with explicit parameters and side-by-side results. |
| `topology` | Periodic graph, connected components under translations, dimensionality, rings, and framework/layer evidence. |
| `layers` | Orientation-aware planes, layer grouping, surface normal, interlayer separation, and vacuum estimates; supersedes no existing axis-gap claim. |
| `compare` | Symmetry-aware matching, RMS displacement, mapping ambiguity, duplicate detection, and tolerance evidence. |
| `transform` | Primitive/conventional, supercell, slab, defect, reorder, coordinate cleanup, and per-step lineage records. |
| `exporters` | QE, VASP, CP2K, SIESTA, and neutral-format structure export without inventing DFT parameters. |
| `reciprocal` | Reciprocal lattice and SeeK-path adapter linked to the exact standardized cell. |
| `diffraction` | XRD/reflection simulation with wavelength, radiation type, broadening, and intensity normalization provenance. |
| `databases` | OPTIMADE/mp-api/COD lookup with stable identifiers, response hashes, cache policy, and network/authentication boundaries. |
| `batch` | Streaming inventory, deduplication, bounded parallelism, resumable manifests, and aggregate failure summaries. |

## Adapter record

Every optional adapter should declare machine-readable metadata equivalent to:

```json
{
  "adapter_id": "stable-lowercase-id",
  "adapter_version": "1.0.0",
  "capability": "coordination.voronoi",
  "maturity": "design-only",
  "dependencies": [{"distribution": "pymatgen", "version": "record-at-runtime"}],
  "input_contract": "structure-manifest@1.0",
  "output_contract": "module-specific-version",
  "mutates_structure": false
}
```

Use the maturity sequence `design-only` → `synthetic-validated` → `format-fixture-validated` → `real-artifact-validated`; add `tool-integration-validated` only when an external executable was actually exercised. Dependency availability never promotes maturity.

## Extension rules

1. Add the module and a local adapter registry entry; avoid adding a new central `if software == ...` chain.
2. Validate options before reading or writing artifacts.
3. Return `pass`, `warn`, `fail`, or `not-run` diagnostics with stable IDs.
4. Add synthetic math tests, format fixtures, negative/fail-closed tests, privacy checks, and a performance-size boundary.
5. For structure mutation, append transformation lineage and a site mapping, generate a new fingerprint, and write a new artifact.
6. For DFT exporters, emit only structural files and provenance. Route calculation parameters to the corresponding calculation Skill.
7. Do not add optional-library objects or absolute paths to the stable manifest. Normalize to JSON values and safe labels.
