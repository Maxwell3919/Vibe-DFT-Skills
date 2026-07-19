# Dataset and leakage rules

## Required identity

Each frame metadata item carries:

- stable `frame_id` and correlation `group_id`;
- exactly one split: `train`, `validation`, `test`, or `ood`;
- structure SHA-256 and label SHA-256;
- reference calculation-record/run SHA-256 and independent scientific-acceptance
  decision SHA-256;
- atom count and ordered unique element inventory;
- one dataset-level reference-protocol SHA-256;
- declared energy, force and optional stress label presence.

Hashes are references, not proof that external bytes resolve. Production promotion
needs bundle resolution and semantic recomputation.

## Grouping policy

All frames that can share information through a common origin stay in one group. This
includes adjacent MD frames, snapshots from one relaxation, perturbations of one
parent, symmetry-equivalent variants, conformers derived from one seed, supercells of
one structure, and active-learning queries from one trajectory segment. A group may
not span train/validation/test/OOD.

Structure hashes detect exact duplication only. They do not detect near-duplicates,
so `group_id` is mandatory even when all structure hashes differ.

The deterministic gate also forbids one `source_run_sha256` from spanning splits.
This catches the mechanically provable case where frames from the same relaxation or
trajectory were assigned different group IDs. Near-related runs still require a
conservative externally generated grouping policy.

## Split roles

- `train`: optimizer input.
- `validation`: early stopping and hyperparameter/model selection.
- `test`: evaluated once after the model and thresholds are frozen.
- `ood`: deliberately shifted domain, never merged into the headline in-domain mean.

The manifest must contain all four for a deployment-oriented workflow. A narrower
training experiment may omit OOD, but then deployment audit is blocked.

## Label and unit policy

Initial candidate units are exact: energy `eV`, forces `eV/angstrom`, stress
`eV/angstrom^3`. Every frame needs energy and forces. Stress is either present for all
frames or absent for all frames; a future missing-label mask requires a separate
schema and provider profile.

All frames share one reference protocol hash. Mixing functionals, pseudopotentials,
cutoffs, spin conventions, charge states, isolated-atom references, stress sign
conventions, or energy offsets under one protocol is blocked.
