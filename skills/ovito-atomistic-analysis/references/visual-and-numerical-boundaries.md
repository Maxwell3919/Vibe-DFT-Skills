# Visual and numerical evidence boundaries

## Visual artifacts

Record at minimum source hashes, selected frames, pipeline/modifier order, provider edition and
version, particle radii/colors, cell display, camera projection/position/direction, viewport size,
background, renderer, lighting, transparency, crop, frame rate, codec, and output hash.

Use visual QA to detect clipping, missing atoms, unexpected periodic images, illegible legends,
camera jumps, color collisions, discontinuities, and corrupted frames. A visually plausible image
does not validate its underlying numerical classification.

## Numerical artifacts

Record units, selectors, neighbor cutoff, reference frame, topology/mapping, PBC/cell policy,
normalization, bins, excluded atoms, per-frame counts, uncertainty or sensitivity checks, and a
comparison to an independent reference where applicable.

Never extract quantitative values by eye when a machine-readable table is available. Never use
color or rendered geometry as the sole evidence for coordination, phase, defect, strain, or
dislocation claims.

## Coupled review

When a figure visualizes a numerical result, require both evidence tracks:

1. validate the numerical artifact and its source lineage;
2. bind the figure to that exact artifact hash and pipeline;
3. perform visual QA;
4. keep the scientific claim pending expert review.

The candidate currently implements neither numerical modifiers nor rendering, so it cannot emit
either evidence track beyond planning.
