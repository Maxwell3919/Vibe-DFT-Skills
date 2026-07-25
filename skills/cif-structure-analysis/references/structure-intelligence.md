# Structure-intelligence methods and boundaries

This reference defines the screening added on top of traceable CIF parsing. Every result describes the selected ASE-materialized periodic model and inherits occupancy, disorder, parser, symmetry-tolerance, and neighbor-definition limitations.

## Quality analysis

`ciftool.quality` compares the declared formula with materialized element counts by reduced ratio, or by formula times `_cell_formula_units_Z` when a positive Z is available. It reports `NOT_COMPARABLE` when formula metadata is absent/unparseable or when partial occupancy/disorder makes a representative-cell comparison misleading. A mismatch is a review warning, not an automatic structural repair.

Cell quality records rank, determinant, and condition number. Configured short contacts are copied into a separate review check. These checks catch malformed or risky starting inputs; they do not evaluate an energy surface.

## Local geometry

`ciftool.local_geometry` expands canonical nearest-neighbor periodic edges into center-to-neighbor vectors. It reports coordination, distance statistics, all pairwise bond angles up to a fixed sample limit, and broad labels such as linear-like, trigonal-planar-like, tetrahedral-like, square-planar-like, or octahedral-like.

The shell is the existing per-center nearest-distance shell within its recorded tolerance. Labels are vector-shape hints, not bond orders, oxidation states, ligand-field assignments, or chemically complete coordination environments.

## Periodic graph dimensionality

`ciftool.topology` creates one periodic graph per configured covalent-radius scale using ASE natural cutoffs. For each connected component it propagates lattice offsets through the graph and measures the rank of nonzero translation cycles:

- rank 0 → finite (`0D`) graph component;
- rank 1 → chain-like (`1D`) periodicity;
- rank 2 → layer-like (`2D`) periodicity;
- rank 3 → framework/bulk-like (`3D`) periodicity.

The top-level candidate is reported only when component rank/size signatures agree across all configured scales. A changing signature returns `SENSITIVE`; multiple stable component ranks return `MIXED`. Edge counts may change without changing the dimensionality signature.

Covalent radii are not universal bond criteria. Ionic, metallic, multicenter, molecular, hydrogen, and weak interlayer interactions can require a different validated graph. A `2D` result is not an exfoliation-energy or physical-vacuum result.

## Symmetry-only property screening

When spglib detects a point group, `ciftool.screening` records:

- centrosymmetry;
- whether ordinary bulk piezoelectricity is symmetry-allowed (all non-centrosymmetric crystallographic point groups except `432`);
- whether the crystallographic point group is polar;
- whether the bulk electric-dipole second-harmonic response is allowed by inversion symmetry.

It also records the cell-length ratio, graph-dimensionality candidate, and the presence of d/f-block elements. These are prioritization hypotheses only. They do not establish a nonzero response, ferroelectric switchability, magnetism, band gap, transport, porosity, exfoliation, or phase stability.

## Optimization starting points

`optimization_guidance` exposes three unranked candidates:

1. the source-as-read structure as immutable provenance anchor and unconstrained baseline;
2. the spglib symmetry-idealized primitive summary, when generated;
3. the spglib symmetry-idealized conventional summary, when generated.

It recommends idealized cells for screening only when the quality screen is not failed, occupancy/disorder is absent, and the detected symmetry is not tolerance-sensitive. It always requires a source baseline and a symmetry-breaking control. Disorder, short contacts, tolerance-sensitive symmetry, or graph sensitivity are explicit blockers; a robust `2D` graph adds a bounded layer-registry comparison cue.

No candidate is energy-ranked. Reducing optimization time requires a later calculation Skill to define the energy/force method, pseudopotential/basis, numerical convergence, cell/position constraints, dispersion treatment where applicable, and independent stability evidence. Never infer the “most stable position” from this artifact alone.
