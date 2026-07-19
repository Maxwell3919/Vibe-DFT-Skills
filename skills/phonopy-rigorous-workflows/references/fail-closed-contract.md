# Fail-closed lineage contract

## Ordered gates

1. **Version gate** — exact Phonopy profile, package digest, and v4 command semantics.
2. **Structure gate** — safe workflow id, separate unit-cell and primitive fingerprints/counts, an explicit nonsingular primitive matrix, unit-cell hash, integer nonsingular supercell matrix, and derived supercell atom count.
3. **Displacement gate** — hashed displacement-set identity; unique displacement ids; one-based atom indices; finite 3-vectors whose norms match the declared displacement distance; unique displaced-supercell hashes.
4. **Force gate** — exactly one record per displacement and no extra record; `eV/angstrom`; `[supercell_atoms, 3]`; raw parent calculation-record hash plus a recomputed semantic projection hash; separate input-validation, output-completion, electronic-convergence, and force-acceptance passes; matching structure fingerprint; input/output/file hashes; canonical ordered collection hash.
5. **Force-constant gate** — full `[supercell_atoms, supercell_atoms, 3, 3]` shape; exact displacement-set and force-collection parent hashes; explicit calculator/symmetrization/ASR declarations.
6. **Product gate** — every requested mesh, band, DOS, or NAC product exists and binds to the exact force-constants hash. DOS also binds to mesh. Parameters, dimensions, units, and artifact hashes are explicit.
7. **NAC gate** — exact Born-charge `[primitive_atoms,3,3]` and dielectric `[3,3]` shapes, finite values, raw source-record hash plus semantic projection hash, matching unit/primitive fingerprints, source acceptance, method, factor/unit convention, and force-constant parent.
8. **Claim gate** — while the package is development/non-routable, every current report remains `no_positive_claim` with promotion/execution unauthorized. Lowest evidence maturity bounds only `future_gate_ceiling`; signed negative frequencies remain visible as data, not a current positive claim.

Weak-model routing consumes [weak-model-decision-table.json](weak-model-decision-table.json) as the only machine source of truth: select the first ascending-priority match and use its final evidence-free default when no earlier condition is established.

## Failure semantics

- Exit `2`: malformed, contradictory, missing, duplicate, dimensionally inconsistent, or hash-incoherent evidence.
- Exit `3`: a requested version/task/adapter is intentionally unsupported or lacks maturity evidence.
- Exit `0`: only the requested technical gate passed.

Do not substitute filenames for hashes, tolerate missing displacements, average duplicate forces, infer units, silently reorder atoms, repair a parent mismatch, discard imaginary frequencies, or treat an ASR/symmetrization flag as proof of convergence.

Report publication is fail closed: reject existing/broken-link targets and every input identity; write, flush, and fsync a same-directory exclusive temporary file; atomically publish only if the target is absent; remove the temporary file on pre-publication failure. A failed write must not leave a target that resembles a complete report.

## Canonical force collection

Sort records by displacement id and serialize a compact JSON array containing only `displacement_id`, force-file SHA-256, raw parent calculation-record SHA-256, parent evidence-projection SHA-256, parent input SHA-256, and parent output SHA-256. SHA-256 those exact UTF-8 bytes. The manifest's `source_force_records_sha256` must equal this value.

## Privacy

Reports expose safe ids, labels, hashes, counts, units, parameters, findings, and limitations only. Absolute paths, host/account names, raw structures, forces, and unpublished values do not enter the public report.
