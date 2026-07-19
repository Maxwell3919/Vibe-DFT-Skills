# Adapter contract

## Scope split

The official feature catalog and tutorial recipes support task discovery and documentation-grounded planning across the software; they do not extend this deterministic adapter. `vaspkit_catalog.py` never launches VASPKIT and blocks feature-only or conflicting task ids. The native adapter/parser below remains limited to the stated task-211/252 synthetic protocol. Keep `official feature listed`, `official recipe established`, `deterministic adapter tested`, and `native binary executed` as four separate fields.

## Parent calculation projection

Require `record_sha256` for the raw accepted VASP record and independently compare `evidence_projection_sha256` with the SHA-256 of compact, UTF-8, key-sorted JSON. The projection is domain-separated by `vasp-calculation-evidence-projection@1.0` and contains `raw_record_sha256`, record id, code/version, structure fingerprint, completion, spin count, exactly four acceptance gates (`input`, `output`, `electronic`, and `band_task`), and file records sorted by role. Each projected file contains exactly role, SHA-256, byte count, and label. File-list order is not semantic; every projected value is semantic. A missing projection, detached raw-record hash, or semantic mutation with a stale projection fails. This hash binding is not a digital signature and does not authenticate who produced the upstream record.

## Planner

`plan-menu` validates the VASP source record, exact profile, and task-specific required roles. It returns `dry_run: true`, `execution_performed: false`, `argv_template: ["<vaspkit-executable>"]`, literal stdin tokens, banner/prompt sentinels, forbidden sentinels, expected outputs, binary identity requirements, and `fresh-directory-or-refuse-existing`. It never runs a process.

The 1.5.0 task-211 and task-252 protocol is synthetic-validated against the official 1.5 documentation. The 1.5.1 profile remains design-only until a version-specific transcript and binary digests exist; do not inherit execution maturity from 1.5.0.

## Transcript

Capture a single invocation with stdin echo and merged terminal output. Read at most 4 MiB, reject invalid UTF-8/NUL/BOM, require exactly one banner/task/default token, preserve official ordered sentinels, and reject `Error`, `Fatal`, segmentation, severe runtime, missing-input, or concatenated runs. Store the private transcript outside Git and publish only its digest and safe event list.

## Band table and labels

Read at most 16 MiB of numeric `BAND.dat`/`BAND_REFORMATTED.dat` rows as one path coordinate plus one or more energy columns. Require constant width, finite values, nondecreasing path coordinate, and a positive total path interval. This candidate supports only `spin_channels: 1`; other layouts block.

Read `KLABELS` as label plus coordinate, ignoring blank/comment/header lines. Require safe labels, finite ordered coordinates inside the band interval, and merge duplicate-coordinate labels explicitly. For profiles whose last stdin token is default `0`, require `input_table_reference: vaspkit-default-fermi-zeroed`. Bind `source_role: DOSCAR` and `source_sha256` to the projected DOSCAR. Require unit `eV` and sign convention `additive`, then apply `energy_relative_ev = energy_input_ev + additive_offset_ev` exactly as declared. A nonzero explicit offset remains allowed but does not weaken DOSCAR lineage. The parser never infers a reference or sign.

## Read and lifecycle boundary

Open every source, transcript, band, or label artifact once with no-follow semantics; hash, verify, and parse the returned bytes rather than reopening a pathname. Never start an external process. Publish a requested report through an exclusive same-directory temporary file, complete write plus file sync, non-overwriting atomic hard link, directory sync, temporary-link cleanup, and a final directory sync. Refuse existing targets, broken symlinks, races, and every input-path identity. All candidate reports, including passes, keep `claim_ceiling: no_positive_claim`, `promotion_authorized: false`, and `execution_authorized: false`. Treat `future_gate_ceiling` as post-promotion potential only.
