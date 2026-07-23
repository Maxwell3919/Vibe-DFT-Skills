# Dataset layout contract

The candidate describes a DeepMD layout without exposing private paths or reading
arrays. Each system has one safe ID, one correlation group and one split.

Required array metadata:

- `coord.npy`: dtype `float32` or `float64`, physical NPY shape
  `[nframes, 3 * natoms]`
- `energy.npy`: same float dtype, shape `[nframes]`
- `force.npy`: same float dtype, physical NPY shape `[nframes, 3 * natoms]`
- `box.npy`: same float dtype, physical NPY shape `[nframes, 9]` for periodic
  systems
- `virial.npy`: same float dtype, shape `[nframes, 9]` when virial policy is
  `all_systems`

These are physical header shapes for the canonical on-disk arrays. The provider's
logical properties remain coordinate/force `[nframes, natoms, 3]` and box
`[nframes, 3, 3]`; its loader restores those tensor dimensions. The version-matched
official `raw_to_set.sh` writes one flattened row per frame with `numpy.loadtxt`, so a
manifest using the logical three-dimensional shapes would reject provider-produced
NPY files. The standard profile normalizes single-frame energy to `[1]`; it does not
accept a zero-dimensional scalar header.

The official NumPy layout stores frame arrays inside one or more `set.*` directories
and root system properties such as `type.raw`, `type_map.raw`, and optional `nopbc`
beside them.
Each `set.*` directory is a storage chunk of the same system, not a statistical split.
A future byte adapter must inventory every set, concatenate only along the frame axis,
and prove that each array family has identical frame counts and compatible dtypes.

For standard systems, every frame has the same atom count and type ordering. Mixed
type data requires `real_atom_types.npy`, descriptor-specific support, and a separate
profile; it is not accepted by this initial standard-layout guard.

Every array record carries exact SHA-256 and byte count. `type.raw` and
`type_map.raw` are separately hash-bound. A future adapter must validate array headers,
type indices, finite values, units and hashes from real bytes.
The metadata gate rejects a byte count smaller than the dense payload implied by
shape and dtype; it does not infer or authenticate the NumPy header.

The layout root binds the exact generic `ml-potential-workflows` dataset-audit report
with `source_dataset_audit_sha256`. Every system additionally binds an ordered
row-to-source record with `source_frame_index_sha256`; that external index must map
each array row to the accepted structure, labels, reference run, decision and group.
These hashes are inventories until a trusted bundle resolver opens and verifies the
referenced bytes.

Exact duplicates are rejected by array hash. Near-duplicates require conservative
correlation groups. A group cannot span train, validation, test and OOD.

Initial units are energy `eV`, force `eV/angstrom`, virial `eV`. Mixed reference DFT
protocols, type-map order or unit conventions require separate datasets.

See [provider operational workflow](operational-workflow.md) for source conversion,
split rendering, virial/stress handling, and practitioner failure checks. Those
heuristics do not enlarge this metadata gate.
