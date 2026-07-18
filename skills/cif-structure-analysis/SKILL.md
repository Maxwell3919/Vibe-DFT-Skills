---
name: cif-structure-analysis
description: Use when analyzing CIF files for code-backed structure facts such as formula, atom counts, cell parameters, volume, density, coordinates, nearest distances, nearest-neighbor element-pair or target bond-length matches, short-distance flags, layer/vacuum estimates, or symmetry attempts.
---

# CIF Structure Analysis

## Overview

Use this skill to analyze CIF files with deterministic Python tooling before making structure claims. The default local helper uses ASE, optional spglib, and Matplotlib to produce JSON, Markdown, and reproducible a/b/c projection artifacts.

## Workflow

1. Identify the input `.cif` path and an output directory.
2. Run the helper before reporting any numeric structure facts:

```bash
python3 ~/.codex/skills/cif-structure-analysis/scripts/analyze_cif.py \
  --input path/to/structure.cif \
  --json path/to/structure.analysis.json \
  --markdown path/to/structure.analysis.md \
  --views-dir path/to/views
```

When the skill is used directly from the source repository rather than an installed symlink, invoke the same bundled script under this skill directory.

3. Read the JSON artifact for exact values, the Markdown artifact for a report-ready summary, and the optional PNG files for a/b/c direction structure views.
4. State limitations from the artifact, including parser warnings, missing optional symmetry support, short-distance flags, or ambiguous layer/vacuum estimates.
5. If the helper exits nonzero or artifacts are missing, return `BLOCK` and do not report numeric structure conclusions.

## Nearest-Neighbor Bond-Length Matching

Filter the computed nearest-neighbor shell by an unordered element pair, a target distance, or both:

```bash
python3 ~/.codex/skills/cif-structure-analysis/scripts/analyze_cif.py \
  --input path/to/structure.cif \
  --json path/to/structure.analysis.json \
  --markdown path/to/structure.analysis.md \
  --match-elements Na-Cl \
  --match-bond-length 2.82 \
  --match-bond-tolerance 0.03
```

- Treat `Na-Cl` and `Cl-Na` as the same element pair.
- Omit `--match-bond-length` to return all nearest-shell bonds for the requested element pair.
- Omit `--match-elements` to search all nearest-shell element pairs around the target distance.
- Read the result at `structure.nearest_distances.bond_length_match`. Report its query, `MATCHED` or `NO_MATCH` status, match count, matching pairs, distances, absolute deltas, and closest candidate when present.
- Do not interpret `NO_MATCH` as an invalid structure. It only means that the defined nearest-neighbor scope contains no bond satisfying the query and tolerance.
- Preserve the reported scope limitation: matching uses unique atom-index pairs and ASE minimum-image distances; it does not enumerate periodic-image multiplicity or self-image neighbors and therefore is not a coordination-number calculation.

To create a compact PPT-style one-page HTML brief after analysis:

```bash
python3 ~/.codex/skills/cif-structure-analysis/scripts/make_structure_deck.py \
  --analysis-json path/to/structure.analysis.json \
  --output path/to/structure.deck.html \
  --title "Structure Analysis"
```

The HTML output is a single 16:9 page containing an interactive rotatable 3D structure, embedded static a/b/c views, and compact report tables. The 3D scene keeps the structure center fixed as the rotation/camera target, provides `a`/`b`/`c` view buttons that reset the camera to the matching projection, draws only the per-atom nearest-neighbor bond shell from `nearest_neighbor_bond_pairs`, and shows bond length on click/tap. It embeds the local Three.js module by default for offline use; pass `--no-inline-three --three-url ...` only when a CDN/module URL is preferred. Verify WebGL rendering with a normal browser or headless Chrome without disabling GPU/WebGL.

## Projection Convention

Use the same convention for script-generated and VESTA-generated three views:

| View | Plane shown | Horizontal axis | Vertical axis | Purpose |
| --- | --- | --- | --- | --- |
| along `a` | `b-c` | `b` | `c` | Side view through the `a` direction. |
| along `b` | `c-a` | `c` | `a` | Side view through the `b` direction. |
| along `c` | `a-b` | `a` | `b` | Top view through the `c` direction. |

For non-orthogonal cells, draw the actual projected cell-vector polygon. Do not replace the `a-b` plane with a rectangular box when `gamma` is not 90 degrees.

Static PNG views should use an atom-extent viewport by default: crop to the projected atom coordinates plus padding so vacuum spacing does not dominate the image. Keep the full cell and vacuum values in JSON/Markdown facts rather than forcing them into the image viewport.

## VESTA Export Option

Use VESTA when the user wants publication-style or manually inspected images. On this machine VESTA is installed at `/Applications/VESTA/VESTA.app`, but no stable `vesta` command-line exporter was found, so treat VESTA output as a manual or GUI-assisted companion artifact rather than the default automated evidence backend.

When using VESTA, export three images with the projection convention above and record:

- VESTA app path and version if visible.
- input CIF path.
- exported image paths.
- view direction for each image.
- any manual style changes such as atom radii, colors, cell display, labels, or background.

Keep the deterministic JSON/Markdown output as the source for numeric structure facts even when VESTA images are present.

## Allowed Claims

- Formula, atom count, and element counts.
- Cell lengths, angles, volume, density, and periodic boundary conditions.
- Coordinate summaries in Cartesian and fractional coordinates.
- Nearest-neighbor distance summaries and suspicious short-distance flags.
- Nearest-neighbor element-pair and target bond-length matches, including explicit tolerance, absolute delta, and closest candidate.
- Axis gap estimates that can help inspect layer/vacuum geometry.
- Symmetry attempt results when optional symmetry support is available.
- Generated PNG projections along a, b, and c when `--views-dir` is supplied.
- VESTA-rendered a/b/c images when their provenance and view convention are recorded.
- PPT-style one-page HTML brief with interactive 3D view when generated from the analysis JSON artifact.

## Forbidden Claims

- Do not provide DFT setup advice, pseudopotential choices, k-point settings, cutoff settings, magnetic initialization, or supercell recommendations.
- Do not judge physical credibility, stability, synthesis feasibility, or calculation readiness.
- Do not treat short-distance flags or layer/vacuum estimates as physics conclusions.
- Do not report values that are not present in the generated artifacts.

## Output Discipline

For every numeric statement, cite the JSON or Markdown artifact path and the command used to generate it. Separate computed facts from interpretations and keep the interpretation bounded to structure inspection only.
