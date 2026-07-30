---
name: cif-structure-analysis
description: Use when parsing or analyzing CIF files for traceable structure facts, data-block and raw-tag metadata, standard uncertainties, occupancy/disorder warnings, periodic-image neighbors and coordination, local geometry hints, multi-scale connectivity dimensionality, symmetry-only property screening, target element-pair or bond-length matching, short-distance flags, symmetry evidence, structure identity, optimization starting-point guidance, axis-gap estimates, or static structure projections.
---

# CIF Structure Analysis

Read [the local official-manual cache route](references/manual-cache-route.md) before using any external standards or library documentation body.

## Purpose

Run the helper before making numeric structure claims. It emits a schema-validated JSON manifest and Markdown summary; optional PNGs are presentation artifacts. It can reject or flag avoidable input problems and propose bounded, unranked optimization starting points. It does not choose DFT parameters, evaluate an energy model, or identify a stable structure.

When this analysis feeds a managed calculation workspace, read [the structure milestone and taskbook route](references/calculation-workspace-and-taskbook.md). Preserve each source/derived structure under a distinct `01-structures` label and append a typed `structure` milestone only after deterministic analysis passes. In review mode, record `pending-review` and pause before any later approval; approval selects reviewed bytes for the next planned step and does not prove stability or scientific acceptance.

## Analyze

Prefer one no-clobber directory bundle:

```bash
python3 scripts/analyze_cif.py \
  --input path/to/structure.cif \
  --bundle-dir path/to/new-analysis-bundle
```

This captures the source once into a task-private immutable snapshot, renders and validates all
artifacts in private staging, and atomically publishes `analysis.json`, `analysis.md`, and
content-derived PNG names. The bundle target must not already exist.

Use loose-file compatibility mode only when a surrounding workflow requires separate paths:

```bash
python3 scripts/analyze_cif.py \
  --input path/to/structure.cif \
  --json path/to/structure.analysis.json \
  --markdown path/to/structure.analysis.md
```

Add `--views-dir path/to/views` for static a/b/c PNGs in loose-file mode. Every target is
no-clobber and the complete target graph is checked before publication. For a multi-block CIF,
use `--block-name NAME` or `--block-index N`; default index is `0`, and the manifest inventories
all blocks. A metadata-only selected block, ambiguous case-insensitive name, or invalid selection
fails without a published artifact set.

Treat the process exit as a separate machine-readable gate: `0` means a `PASS` or `WARN`
artifact set was published, `3` means a diagnostic `BLOCK` artifact set was published, `2`
means argument/input/output preflight refusal, and `1` means an analysis, rendering, or
publication runtime failure. Never discard a published `BLOCK` bundle merely because its exit
is nonzero.

Use `--topology-scale-factors 1.0 1.15 1.3` to change the covalent-radius sensitivity sweep. Keep more than one scale when using a dimensionality candidate: `SENSITIVE` is an evidence result, not an error to suppress.

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

## Screen the structure before DFT

Read these independent payloads:

- `structure.quality_analysis`: formula/Z versus the materialized cell when comparable, cell rank/conditioning, short contacts, occupancy, and disorder review needs.
- `structure.screening_eligibility`: independent scope gates for artifact generation, geometry screening, symmetry-property screening, connectivity screening, and calculation handoff.
- `structure.local_geometry`: per-site nearest-shell distances, angles, coordination, and geometric hints.
- `structure.connectivity_analysis`: periodic connected components and translation-rank dimensionality across configured covalent-radius scales.
- `structure.property_screening`: point-group permission/forbidden screens, metric anisotropy, dimensionality, and d/f-block presence as structure-only hypotheses.
- `structure.optimization_guidance`: source, primitive, and conventional starting-point candidates plus required controls and blockers.

Treat all six as screening. Eligibility is scope-specific: one scope can be `PASS` while another
is `WARN`, `BLOCK`, or `NOT_ASSESSED`. A geometry hint is not a bond-order assignment; graph
dimensionality is not exfoliation evidence; a symmetry-allowed response is not a nonzero
coefficient; d/f-block presence is not magnetism; and an available standardized cell is not a
lower-energy structure.

Optimization candidates are intentionally `NOT_RANKED`, with `stability_assessed=false` and `energy_model_used=false`. Retain the source structure as the provenance baseline. When an idealized cell is used, compare it with a lower-symmetry control under the same accepted energy/force method. Resolve occupancy/disorder and short-contact blockers before expensive relaxation.

## Evidence workflow

1. Check top-level `status` and every `validation.checks` entry.
2. Confirm source SHA-256, selected block, parser, dependency versions, options, and
   `analysis_key`. Reuse a parent audit only when its full `analysis_key` matches; path or mtime
   equality is not a cache key.
3. Separate raw `document.metadata` from the ASE-materialized `structure`.
4. For occupancy/disorder warnings, state that formula, density, neighbors, and symmetry describe a representative model, not a resolved ensemble.
5. Report spglib version, tolerances, declared comparison, and tolerance sensitivity with symmetry claims.
6. Report the topology scale factors and whether the candidate is stable across them.
7. Preserve every scoped eligibility result, `NOT_RANKED`, blockers, and claim boundaries when
   handing starting points to a calculation Skill.
8. Cite the JSON or Markdown artifact for each numeric claim. Return `BLOCK` when the helper
   exits `3`, output is missing, artifact status is `BLOCK`, or another nonzero exit leaves no
   validated artifact set.

Read [structure-manifest.md](references/structure-manifest.md) for field and lineage semantics, [structure-intelligence.md](references/structure-intelligence.md) for screening methods and their limits, [dependencies-and-capabilities.md](references/dependencies-and-capabilities.md) for library boundaries, and [extension-interfaces.md](references/extension-interfaces.md) before adding modules.

## Static projection convention

| View | Plane | Horizontal | Vertical |
| --- | --- | --- | --- |
| along `a` | `b-c` | `b` | `c` |
| along `b` | `c-a` | `c` | `a` |
| along `c` | `a-b` | `a` | `b` |

Non-orthogonal projections use actual cell vectors. PNGs crop to atom extent; full cell facts remain in JSON/Markdown.

## Claim boundaries

Only claim fields present in a non-`BLOCK` artifact.

Do not treat axis gaps as rigorous layer/vacuum thickness; treat flags, coordination, local geometry, graph dimensionality, detected symmetry, property hypotheses, standardized cells, or `NO_MATCH` as stability conclusions; claim dictionary validation, magnetic/modulated support, structure equivalence, ring/framework identity, XRD, or database identity without a validated extension; or provide pseudopotential, cutoff, k-point, magnetic, convergence, supercell, or other DFT setup advice.
