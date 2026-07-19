# Dataset layout contract

The candidate describes a DeepMD layout without exposing private paths or reading
arrays. Each system has one safe ID, one correlation group and one split.

Required array metadata:

- `coord.npy`: dtype `float32` or `float64`, shape `[nframes, natoms, 3]`
- `energy.npy`: same float dtype, shape `[nframes]`
- `force.npy`: same float dtype, shape `[nframes, natoms, 3]`
- `box.npy`: same float dtype, shape `[nframes, 3, 3]` for periodic systems
- `virial.npy`: same float dtype, shape `[nframes, 9]` when virial policy is
  `all_systems`

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
