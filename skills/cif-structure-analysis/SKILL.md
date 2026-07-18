---
name: cif-structure-analysis
description: Use when parsing or analyzing CIF files for traceable structure facts, data-block and raw-tag metadata, standard uncertainties, occupancy/disorder warnings, periodic-image neighbors and coordination, target element-pair or bond-length matching, short-distance flags, symmetry evidence, structure identity, axis-gap estimates, or static structure projections.
---

# CIF Structure Analysis

## Purpose

Run the helper before making numeric structure claims. It emits a schema-validated JSON manifest and Markdown summary; optional PNGs are presentation artifacts. This Skill does not choose DFT parameters or judge stability.

## Analyze

```bash
python3 scripts/analyze_cif.py \
  --input path/to/structure.cif \
  --json path/to/structure.analysis.json \
  --markdown path/to/structure.analysis.md
```

Add `--views-dir path/to/views` for static a/b/c PNGs. For a multi-block CIF, use `--block-name NAME` or `--block-index N`; default index is `0`, and the manifest inventories all blocks. Invalid selection fails without JSON/Markdown output.

## Match near-neighbor lengths

```bash
python3 scripts/analyze_cif.py \
  --input path/to/structure.cif \
  --json path/to/structure.analysis.json \
  --markdown path/to/structure.analysis.md \
  --match-elements Na-Cl \
  --match-bond-length 2.82 \
  --match-bond-tolerance 0.03
```

- Element pairs are unordered. Omit target length to return the requested pair; omit elements to search all species near the target.
- Read `structure.nearest_distances.bond_length_match`. `NO_MATCH` only describes this query and tolerance.
- Edges explicitly enumerate periodic and self images. `(i,j,S)` and `(j,i,-S)` are one undirected edge; distinct shifts remain distinct.
- Coordination counts directed neighbors in each site's nearest-distance shell. It is geometric coordination, not bond order.
- Use `--neighbor-cutoff` only for an intentional fixed cutoff; otherwise search expands to `--maximum-neighbor-cutoff`. Incomplete search gives `WARN`.

## Evidence workflow

1. Check top-level `status` and every `validation.checks` entry.
2. Confirm source SHA-256, selected block, parser, dependency versions, and options.
3. Separate raw `document.metadata` from the ASE-materialized `structure`.
4. For occupancy/disorder warnings, state that formula, density, neighbors, and symmetry describe a representative model, not a resolved ensemble.
5. Report spglib version, tolerances, declared comparison, and tolerance sensitivity with symmetry claims.
6. Cite the JSON or Markdown artifact for each numeric claim. Return `BLOCK` when the helper fails, output is missing, or artifact status is `BLOCK`.

Read [structure-manifest.md](references/structure-manifest.md) for field and lineage semantics, [dependencies-and-capabilities.md](references/dependencies-and-capabilities.md) for library boundaries, and [extension-interfaces.md](references/extension-interfaces.md) before adding modules.

## Static projection convention

| View | Plane | Horizontal | Vertical |
| --- | --- | --- | --- |
| along `a` | `b-c` | `b` | `c` |
| along `b` | `c-a` | `c` | `a` |
| along `c` | `a-b` | `a` | `b` |

Non-orthogonal projections use actual cell vectors. PNGs crop to atom extent; full cell facts remain in JSON/Markdown.

## Claim boundaries

Only claim fields present in a non-`BLOCK` artifact.

Do not treat axis gaps as rigorous layer/vacuum thickness; treat flags, coordination, detected symmetry, or `NO_MATCH` as stability conclusions; claim dictionary validation, magnetic/modulated support, equivalence, topology, XRD, or database identity without a validated extension; or provide pseudopotential, cutoff, k-point, magnetic, convergence, supercell, or other DFT setup advice.
