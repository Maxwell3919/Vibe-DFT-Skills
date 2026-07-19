# Planner and parser adapter contract

## Dry-run planning

`plan-stage` validates the complete manifest first, then emits an exact-version argv template. It never substitutes real paths or starts a process. Version 4.3.1 plans use `phonopy-init` for displacement/force collection and `phonopy` for mesh/band/DOS/NAC products. The planner never emits the removed `--nac` option; NAC is represented by parameters already bound into the input evidence.

Each plan records `dry_run: true`, `execution_performed: false`, exact profile, manifest hash, ordered argv tokens, required inputs, expected outputs, overwrite boundary, and claim ceiling. A future executor must use a fresh working directory or explicitly refuse every pre-existing output.

## Frequency table

The parser accepts an explicit interchange format:

```text
# phonopy_frequency_table_v1 kind=band unit=THz parent_force_constants_sha256=<sha256>
1 1 0.0 0.0 0.0 -0.10 1.0
1 2 0.0 0.0 0.0  0.20 1.0
```

Columns are `point_index mode_index qx qy qz frequency weight`. Require a single header, exact artifact bytes/hash, exact product frequency unit, finite values, contiguous point and mode indices, exactly `3 * primitive_atoms` modes per point, identical q coordinates/weight within each point, nonnegative weights, and the exact force-constant parent hash. For band tables, require the complete linearly sampled q path declared by the versioned segment/point parameters. Preserve negative frequencies and report their count.

The table is a controlled handoff, not a universal YAML/HDF5 parser. Native `band.yaml`, `mesh.yaml`, HDF5, eigenvectors, and DOS tables remain blocked until a version-matched parser and legal format/real fixtures are added.
