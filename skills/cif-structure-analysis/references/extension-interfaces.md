# CIF extension interfaces

## Implemented modules

- `ciftool.document`: syntax routing, data-block selection, raw metadata, uncertainty, occupancy/disorder, and tag inventory.
- `ciftool.snapshot`: bounded one-descriptor input capture and task-private immutable parser bytes.
- `ciftool.artifacts`: no-clobber loose-set publication and atomic no-replace directory bundles.
- `ciftool.neighbors`: periodic-image enumeration, canonical edges, nearest shells, coordination, short-distance flags, and target bond-length matching.
- `ciftool.symmetry`: spglib evidence, declaration comparison, tolerance sweep, and standardized-cell summaries.
- `ciftool.quality`: formula/Z materialization consistency, cell numerics, and short-contact/occupancy/disorder screening.
- `ciftool.local_geometry`: nearest-shell distance/angle summaries and explicitly heuristic geometry labels.
- `ciftool.topology`: covalent-radius periodic graphs, connected components, and translation-rank dimensionality sensitivity.
- `ciftool.screening`: symmetry-only property hypotheses and unranked optimization starting-point guidance.
- `ciftool.eligibility`: independent artifact, geometry, symmetry-property, connectivity, and calculation-handoff scope gates.
- `ciftool.manifest`: safe provenance, structure and analysis identities, validation aggregation, element styles, relative artifacts, and schema validation.
- `analyze_cif.py`: the orchestration CLI and Markdown/static-PNG presentation layer.

Keep parsing, scientific analysis, presentation, and external tool execution separate. A new module must return structured payload plus diagnostics; it must not print claims or mutate another module's result silently.

## Reserved modules

| Module | Contract responsibility |
| --- | --- |
| `quality-extensions` | Duplicate/equivalent-site detection and dictionary-validation adapters beyond the implemented formula/Z, cell, contact, occupancy, and disorder checks. |
| `coordination-extensions` | Named alternative distance, Voronoi, CrystalNN, or ChemEnv methods with explicit parameters and side-by-side results; never overwrite the implemented nearest-shell result. |
| `topology-extensions` | Ring statistics, named framework/layer identity, bonded-subgraph chemistry, and energetic layer evidence beyond the implemented radius-sensitive translation rank. |
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
