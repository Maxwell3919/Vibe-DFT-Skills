# OVITO analysis recipes and validation guide

## Contents

1. [Status and provider boundary](#status-and-provider-boundary)
2. [Import, mapping, PBC, and trajectories](#import-mapping-pbc-and-trajectories)
3. [Pipeline and modifier order](#pipeline-and-modifier-order)
4. [Selection and deletion](#selection-and-deletion)
5. [Numerical analysis recipes](#numerical-analysis-recipes)
6. [Trajectory averaging, rendering, and export](#trajectory-averaging-rendering-and-export)
7. [Validation and failure modes](#validation-and-failure-modes)
8. [Operational heuristics](#operational-heuristics)
9. [Primary sources](#primary-sources)

## Status and provider boundary

Use this guide to design or review a trusted OVITO 3.15.5 workflow. The call shapes below are
documented provider interfaces; they do not authorize this development candidate to run any
plan-only modifier, render, or export. No native OVITO import or analysis was performed while
writing this guide.

The official provider distinguishes three surfaces:

| Surface | Official 3.15.5 boundary | This candidate |
|---|---|---|
| standalone `ovito` Python module | free, MIT-licensed, installed with `pip install -U ovito`; exposes all data-analysis, visualization, and rendering APIs, including capabilities exclusive to the Pro desktop GUI | internal profile `ovito-basic`; only frame metadata is executable after explicit authorization |
| OVITO Basic desktop | binary distributed under MIT terms; features without a `pro` badge in the joint manual | no GUI execution |
| OVITO Pro desktop and `ovitos` | proprietary desktop license and activation; adds GUI features marked `pro`, integrated Python, renderers, remote rendering, and other tooling | planning only; never executed |

The vendor `ovito` conda package contains the Python module and Pro desktop application; the
desktop requires a paid license. The similarly named conda-forge package contains Basic desktop
only and no Python module. Package presence, application presence, module import, desktop edition,
and license entitlement are separate evidence.

Atomic strain and DXA are not marked Pro-only in the 3.15.5 desktop manual and are also available
through the standalone Python module. Time averaging is marked Pro in the desktop GUI, but its
Python modifier is available in the standalone module. Some rendering engines and desktop
workflows are Pro-only; the Python module nevertheless exposes rendering capabilities. Apply the
candidate's stricter plan policy separately from these official feature facts.

## Import, mapping, PBC, and trajectories

### Official behavior

`ovito.io.import_file()` returns a `Pipeline`, not a computed structure. The source and modified
states are different:

```python
from ovito.io import import_file

pipeline = import_file('trajectory.extxyz', sort_particles=False)
raw = pipeline.source.compute(frame)
result = pipeline.compute(frame)
```

`pipeline.source.compute(frame)` evaluates the file source without downstream modifiers;
`pipeline.compute(frame)` evaluates the complete current pipeline and returns an independent
`DataCollection`. Non-interactive `compute()` defaults to frame 0. Valid frame indices are
`0..pipeline.source.num_frames-1`. A later pipeline edit requires a new `compute()` call; do not
reuse an earlier snapshot as though it changed in place.

OVITO normally preserves the storage order of imported particles. When a unique input ID is
mapped to `Particle Identifier`, `sort_particles=True` can reorder particles by ID. Keep it false
when source order is evidence. Use stable identifiers for cross-frame/reference mapping whenever
possible; without them, algorithms may assume equal counts and unchanged storage order.

For a plain columnar file, map every column explicitly and use `None` to skip a field:

```python
pipeline = import_file(
    'trajectory.xyz',
    columns=[
        'Particle Type', 'Position.X', 'Position.Y', 'Position.Z',
        'Particle Identifier', None,
    ],
    sort_particles=False,
)
```

Use exact standard property names. In LAMMPS dump input, standard fields normally map `id` to
`Particle Identifier`, `type`/`element` to `Particle Type`, coordinates to `Position`, and image
flags to `Periodic Image`; inspect the computed properties rather than relying on a guessed map.

Extended XYZ declares columns with `Properties=name:type:count` triplets. Its cell record is a
3x3 matrix with vectors as columns and values in Fortran column-major order:

```text
Lattice="ax ay az bx by bz cx cy cz"
```

If `Lattice` is present but `pbc` is absent, the official reader assumes all three directions are
periodic. This candidate rejects that implicit default. Basic XYZ has neither a physical length
unit nor a valid periodic cell; a generated bounding box is useful for visualization, not a
replacement for the simulation cell.

For separate topology and coordinates, import the topology first and append a
`LoadTrajectoryModifier` whose source loads the trajectory. It replaces static positions and can
change the pipeline's frame count. Verify identifier, particle-count, type, bond, and frame-time
alignment after composition.

### Required import record

Record input bytes/hash, reader/format, reader options, column-to-property map, skipped columns,
particle count and property schema per frame, ID uniqueness and continuity, source order policy,
cell vectors/origin/PBC per frame, physical units from the producing code, frame index/time/step,
and any topology/trajectory merge.

## Pipeline and modifier order

### Official behavior

OVITO evaluates a pipeline from source to head. In Python, modifiers execute in the order they are
appended. In the desktop pipeline editor, the data flows from the bottom source upward through the
modifier list. Modifier order changes both values and element populations.

For reference-configuration modifiers, modifiers before the reference modifier can affect both
the current and same-pipeline reference configurations. Modifiers after it affect only the
result. An external reference source has its own import identity and settings.

Use this dependency pattern unless the scientific task requires another order:

```text
source/mapping -> unwrap or cell policy -> full-neighborhood analysis -> selection -> deletion
-> aggregate/table -> time average -> visualization -> export
```

Place CNA, PTM, RDF/coordination, strain, and DXA before deleting atoms when they require complete
neighborhoods. If `only_selected=True` is intentional, record what unselected atoms mean: several
modifiers treat them as absent, not merely hidden.

After every `compute(frame)`, inspect the output property names, global attributes, and table keys.
Do not assume a modifier ran because it appears in the pipeline editor or because a prior cached
snapshot contains a similarly named property.

## Selection and deletion

### Official behavior

Selection modifiers create or replace a `Selection` property. Downstream modifiers read that
property only when configured to operate on selected elements. `DeleteSelectedModifier` removes
selected elements from downstream data; it does not rewrite the source file.

Documented Python shape:

```python
from ovito.modifiers import ExpressionSelectionModifier, DeleteSelectedModifier

pipeline.modifiers.append(
    ExpressionSelectionModifier(expression='StructureType == 0')
)
pipeline.modifiers.append(DeleteSelectedModifier())
filtered = pipeline.compute(frame)
```

Expressions use OVITO's exposed property/component names, which can differ from display labels.
Evaluate and record the selected count before deletion. If a later modifier needs original
neighbors, move deletion later or create a separate pipeline branch.

## Numerical analysis recipes

All recipes in this section are **documented, plan-only behavior** for this candidate. For every
accepted numerical result, preserve exact modifier class, parameters, order, input selectors,
frame/reference identity, output property/table names, units, and provider version.

### Coordination and radial distribution function

In 3.15.5 the relevant Python class is `RadialDistributionFunctionModifier`:

```python
from ovito.modifiers import RadialDistributionFunctionModifier

pipeline.modifiers.append(
    RadialDistributionFunctionModifier(cutoff=5.0, number_of_bins=200)
)
data = pipeline.compute(frame)
coordination = data.particles['Coordination']
rdf_table = data.tables['coordination-rdf']
```

The modifier requires `Position`; partial RDF additionally requires `Particle Type`, and
`only_selected=True` requires `Selection`. It emits per-particle `Coordination`, optional
`Per Type Coordination`, and table `coordination-rdf`. The cutoff controls both neighbor counting
and RDF range. Record cutoff in source length units, bin count/width, PBC/cell, type-pair ordering,
selection, and normalization.

### Common neighbor analysis

`CommonNeighborAnalysisModifier` emits integer `Structure Type`, global counts, and the
`structures` table. Recognized types are Other, FCC, HCP, BCC, and ICO. Available modes are
`FixedCutoff`, `AdaptiveCutoff` (the 3.15.5 default), `IntervalCutoff`, and `BondBased`; the last
requires input bond topology.

Record mode and cutoff/bond-generation provenance. Run on the full intended neighborhood before
deletion. CNA is a local structural classifier, not a phase proof; thermal disorder, surfaces,
strain, chemistry, and cutoff choice change classification.

### Polyhedral template matching

`PolyhedralTemplateMatchingModifier` classifies enabled templates among Other, FCC, HCP, BCC,
ICO, simple cubic, cubic/hexagonal diamond, and graphene. Only FCC/HCP/BCC are enabled initially
in the documented API; explicitly enable every intended template. Optional outputs include RMSD,
interatomic distance, orientation, elastic deformation gradient, and chemical ordering.

Record enabled templates, RMSD cutoff, optional outputs, selection, and type mapping. Inspect the
RMSD distribution and classification stability across a justified threshold range. PTM orientation
or deformation output is a local template fit, not automatically a continuum strain field.

### Displacement vectors

`CalculateDisplacementsModifier` compares current and reference positions and emits
`Displacement` and `Displacement Magnitude`. The reference defaults to frame 0 unless changed to
an external or sliding reference. Mapping uses `Particle Identifier` when available; otherwise
equal particle count and storage order are assumptions.

Choose the minimum-image convention for wrapped trajectories and turn it off for already unwrapped
coordinates. A displacement exceeding half the periodic cell cannot generally be reconstructed
from wrapped endpoints alone; unwrap the trajectory using valid image/crossing information first.
For changing cells, record whether affine mapping is off, maps the current cell to the reference,
or maps the reference to the current cell.

### Atomic strain

`AtomicStrainModifier` fits a local deformation gradient between current and reference
neighborhoods and can output Green-Lagrange strain, shear/volumetric strain, deformation gradient,
and non-affine squared displacement (`Dmin2`) depending on options. It requires a sufficiently
large cutoff and enough non-coplanar neighbors. It shares the reference, ID mapping, PBC, and
affine-cell choices of displacement analysis.

Record strain measure, cutoff, reference, affine mapping, neighbor sufficiency/failure flags, and
all optional output toggles. Compare cutoff choices around a structurally justified neighbor shell.
Do not interpret large values at surfaces, vacancies, or unmatched atoms without checking fit
quality and neighbor count.

### Wigner-Seitz defect analysis

`WignerSeitzAnalysisModifier` assigns current atoms to sites of a perfect reference and reports
vacancy/interstitial counts. In site-output mode it replaces the particle collection with reference
sites and their `Occupancy`, which directly represents vacancies. With displaced-atom output it
keeps current atoms and can add `Occupancy`, `Site Index`, `Site Identifier`, and `Site Type`, but
vacant reference sites are not present as particles.

Record the perfect-reference hash, reference/current frame, ID and cell mapping, affine mapping,
per-type occupancy setting, and global counts. A strained or phase-transformed cell can produce
mapping artifacts if the affine policy is wrong. Site assignment identifies reference occupancy;
it does not establish defect formation energy or kinetic mechanism.

### Dislocation extraction analysis

`DislocationAnalysisModifier` (DXA) requires an explicit input crystal structure. It produces a
`DislocationNetwork`, total and type-resolved line lengths, and cell-volume/count attributes. The
official manual estimates roughly 1 kB of working memory per input atom. Record crystal type,
trial-circuit and stretchability settings, selection, line smoothing/coarsening, and memory budget.

DXA uses the left-hand start-finish convention. Reversing a line direction changes the associated
Burgers-vector sign, so do not compare raw signed vectors across frames without orientation
matching. Smoothing and coarsening change displayed line geometry. DXA is a topology/classification
algorithm for supported crystals, not independent proof of a physical dislocation network.

## Trajectory averaging, rendering, and export

### Time averaging

`TimeAveragingModifier` averages an upstream property, attribute, or table over a frame interval.
For example, the official RDF workflow uses:

```python
from ovito.modifiers import TimeAveragingModifier

pipeline.modifiers.append(
    TimeAveragingModifier(operate_on='table:coordination-rdf')
)
averaged = pipeline.compute().tables['coordination-rdf[average]']
```

Averaging per-particle properties requires a constant element population. Place averaging before
deletion that changes count, or average aggregate tables instead. Position averaging under PBC
requires unwrapped trajectories. Tables need a fixed x grid/range across frames. Record frame
interval, stride, sample count, missing-frame policy, upstream key, and emitted `[average]` key.

### Rendering

A pipeline must be added to the scene before `Viewport.render_image()` or animation rendering.
Record viewport type before configuring camera fields, projection, camera position/direction,
field of view, output size, background/alpha, renderer, lighting, particle/bond/cell visual
settings, selected frame range, FPS, codec, and output hash. OpenGL may fail on headless systems;
use and record a supported non-interactive renderer rather than silently changing visual output.

Desktop Tachyon, OSPRay, VisRTX, remote trajectory video, and multi-viewport layout features are
listed as Pro capabilities. The standalone Python module exposes rendering APIs without a desktop
license, but renderer/platform availability still requires a live probe. This candidate keeps
rendering plan-only and conservatively requires its `ovito-pro` planning profile.

### Export

`ovito.io.export_file()` can consume a `Pipeline` or a computed `DataCollection`. A pipeline can
export multiple frames; a `DataCollection` is one static snapshot. Declare format, exact property
columns or table key, precision, selected frame/range/stride, and whether multiple frames are
enabled. Example table shape:

```python
from ovito.io import export_file

export_file(
    pipeline,
    'rdf.txt',
    'txt/table',
    key='coordination-rdf[average]',
)
```

Formats do not preserve every property. Re-import or independently parse the exported artifact,
verify row/frame counts and identifiers, and hash it. Never overwrite the source trajectory.

## Validation and failure modes

Before accepting an OVITO-derived observable:

1. verify exact input hash, provider/module version, edition surface, and operation order;
2. inspect source and computed property schemas, particle counts, IDs, PBC, and cell per frame;
3. verify reference identity and mapping for all comparative modifiers;
4. vary every scientific cutoff/threshold over a justified range and report stability;
5. compare selected frames to an independent calculation or analytically known fixture;
6. retain per-frame failures, unclassified counts, fit failures, and empty selections;
7. export labeled numerical data before rendering and bind the figure to that data hash;
8. reparse exports and keep visual QA separate from numerical validation.

Fail closed on these common states:

| State | Consequence |
|---|---|
| wrong or implicit column mapping | properties/IDs are semantically wrong even if import succeeds |
| missing or duplicated identifiers | cross-frame/reference mapping is unresolved |
| reordered atoms without IDs | displacement, strain, and defect assignments are invalid |
| implicit PBC, cell, or length unit | all distance-based outputs are unresolved |
| delete/select before neighbor analysis | neighborhoods and denominators change |
| wrong reference frame or affine mapping | displacement/strain/defect results answer another question |
| wrapped coordinates used for long displacement or mean position | discontinuities alias the result |
| unstable cutoff/RMSD/fit settings | classification or strain is not robust |
| headless renderer or codec substitution | image/video provenance changed |
| export omits a property or frame | output is incomplete despite successful return |
| pipeline changed without recomputation | inspected snapshot is stale |

## Operational heuristics

These practices are general atomistic-analysis experience, not official OVITO guarantees:

- Start with one representative bulk frame, one boundary/defect frame, and one trajectory edge
  frame before processing all frames.
- Plot an RDF and inspect its first minimum as an initial neighbor-cutoff candidate; then test a
  range and validate against known coordination. The minimum is not an automatic universal cutoff.
- Prefer stable simulation IDs over sorting by storage order. If the producer lacks IDs, generate
  and validate them at the source rather than retrofitting nearest-neighbor identities after motion.
- Keep an unfiltered analysis branch and a presentation branch. Deletion useful for visualization
  should not silently change numerical neighborhoods.
- For thermal structures, compare CNA and PTM classifications and report unclassified fractions;
  disagreement is diagnostic, not a reason to choose the prettier image.
- Sample raw and unwrapped coordinates together when validating displacement or time averaging.
- Save aggregate tables and parameter manifests in addition to `.ovito` sessions and figures;
  session files alone are not portable numerical evidence.

## Primary sources

Checked against first-party OVITO 3.15.5 documentation on 2026-07-22:

- Python module overview and installation:
  https://www.ovito.org/docs/current/python/introduction/introduction.html and
  https://www.ovito.org/docs/current/python/introduction/installation.html
- file I/O and pipeline APIs: https://www.ovito.org/docs/current/python/modules/ovito_io.html and
  https://www.ovito.org/docs/current/python/modules/ovito_pipeline.html
- modifier API: https://www.ovito.org/docs/current/python/modules/ovito_modifiers.html
- XYZ/extxyz and LAMMPS dump readers:
  https://www.ovito.org/manual/reference/file_formats/input/xyz.html and
  https://www.ovito.org/manual/reference/file_formats/input/lammps_dump.html
- pipeline order: https://www.ovito.org/manual/usage/pipeline.html
- CNA, PTM, displacement, atomic strain, Wigner-Seitz, and DXA manual pages under
  https://www.ovito.org/docs/current/reference/pipelines/modifiers/
- rendering and export:
  https://www.ovito.org/docs/current/python/introduction/rendering.html and
  https://www.ovito.org/manual/usage/export.html
- Basic/Pro and licenses: https://www.ovito.org/manual/ovito_pro.html and
  https://www.ovito.org/manual/licenses/index.html
