---
name: dft-structure-preparation
description: Audit and prepare traceable periodic or molecular structures with deterministic identity, periodic-image, occupancy, symmetry, charge/spin, atom-mapping, transformation, round-trip, and DFT export-planning gates. Use when a CIF-derived or normalized structure must be wrapped, reordered, replicated, compared, or handed toward QE, VASP, CP2K, or SIESTA without losing site identity or inventing backend results. This is an isolated development Skill and must not be routed as an active production skill.
---

# DFT Structure Preparation

## Hold the authority boundary

Treat this directory as a non-routable candidate. Never describe it as installed, active,
scientifically accepted, or backend-integrated. Use its deterministic CLI for candidate-local
evidence only. Require the active CIF analysis skill to parse raw CIF syntax and require the
target rigorous-calculation skill to own code-specific parameters.

Separate four roles throughout the workflow:

1. Let the router select a task profile without changing files.
2. Let the deterministic CLI parse, gate, transform, and serialize.
3. Let an optional pinned backend provide only evidence it actually computed.
4. Let a reviewer decide whether a technically eligible structure is scientifically usable.

Do not merge these roles or infer a missing result from a plan, dependency probe, or file name.

## Route the request

Choose exactly one primary route:

- Use `audit` for identity, periodicity, coordinate, occupancy, symmetry, charge, and spin gates.
- Use `roundtrip` to distinguish exact representation, periodic equivalence, and loss.
- Use `transform` only for the implemented `wrap`, `reorder`, or diagonal `supercell` operations.
- Use `plan-export` to create a non-executed QE/VASP/CP2K/SIESTA structure handoff plan.
- Use `probe-backends` to inspect distribution metadata without importing or executing a backend.

Read [workflow.md](references/workflow.md) before transforming data. Read
[data-contracts.md](references/data-contracts.md) before adapting shared repository records.
Read [fail-closed-contract.md](references/fail-closed-contract.md) whenever a gate or dependency
is unresolved. For mechanical routing, parse the machine-readable
[decision table](references/weak-model-decision-table.json) and never take an action stronger than
its `minimum_next_action`.

## Execute the low-reasoning workflow

1. Inventory inputs. Record only a content-derived source label, raw-byte SHA-256, and byte count;
   never expose a user filename or absolute path in an artifact.
2. Normalize upstream data into [the candidate input schema](schemas/structure-preparation-input.schema.json).
   Do not call a candidate-local envelope a shared `structure-snapshot@1.0` record.
3. Run the deterministic gate before interpreting geometry:

   ```bash
   python3 scripts/structure_prepare.py audit INPUT.json --out AUDIT.json
   ```

4. Inspect `status`, `calculation_readiness`, every finding, `claim_ceiling`,
   `future_gate_ceiling`, `promotion_authorized`, and `execution_authorized` even when exit is
   zero. Add `--require-calculation-ready` for an export-bound workflow. Every current candidate
   report must remain `claim_ceiling=no_positive_claim`.
5. For mutation, preserve the input and write one new result envelope:

   ```bash
   python3 scripts/structure_prepare.py transform INPUT.json --operation wrap --out WRAP.json
   python3 scripts/structure_prepare.py transform INPUT.json --operation reorder --order Si-1,Si-0 --out REORDER.json
   python3 scripts/structure_prepare.py transform INPUT.json --operation supercell --repeat 2 1 1 --out SUPERCELL.json
   ```

6. Verify parent/child identity, complete `site_mapping`, image shifts, occupancy findings, and
   round-trip classification. Treat supercell as a derived structure, never an equivalent
   round-trip.
7. Plan a DFT handoff only after readiness is explicit:

   ```bash
   python3 scripts/structure_prepare.py plan-export INPUT.json --target qe --out EXPORT-PLAN.json
   ```

8. Hand the plan and source structure to the target rigorous-calculation skill. Do not generate
   pseudopotentials, basis choices, k-points, cutoffs, charge conventions, or spin settings here.

## Apply the non-negotiable gates

- Preserve mixed and partial occupancy; block calculation readiness until a physical disorder or
  vacancy model is chosen.
- Require unique stable `site_id` values and keep site order in a separate fingerprint.
- Require periodicity, structure kind, cell rank, nonsingular cell, fractional coordinates, and
  Cartesian coordinates to agree within an explicit tolerance.
- Record a periodic image as an integer image shift; never count it as a created atom.
- Invalidate symmetry after a supercell operation until a pinned backend recomputes it.
- Require backend name and version before accepting a `verified` symmetry declaration.
- Check molecular charge/multiplicity parity when a full integer electron count is available.
- Refuse symlink or changing inputs, duplicate JSON keys, non-finite values, unsafe identifiers,
  oversized JSON, existing or evidence-alias outputs, and symlinked output parents.
- Never overwrite a source or output artifact.

## Interpret evidence conservatively

The structure fingerprint is order-independent and periodic-image canonicalized. The site-order
fingerprint records atom order. The representation fingerprint records coordinates, order, and
symmetry representation. Equality of only one digest does not imply equality of the others.

An exit-zero audit proves only that the requested local parsing and gate operation completed. It
does not imply `calculation_readiness=ready`. It never proves that a DFT calculation will converge
or that the modeled chemistry is correct. While this directory is in development and non-routable, the
current ceiling is always `no_positive_claim`; `future_gate_ceiling=input_gates_only` describes
only a possible post-promotion local gate and never upgrades the current claim.

Consult [task-profiles-and-maturity.md](references/task-profiles-and-maturity.md) before quoting a
maturity level. Consult [finding-catalog.md](references/finding-catalog.md) before suppressing or
reclassifying a finding. Do not raise a task above its weakest evidence axis.

## Respect backend and license boundaries

Run `probe-backends` only as a metadata probe. A detected distribution is not an imported module,
a successful operation, a license decision, or integration evidence. Read
[official-sources-and-environment.md](references/official-sources-and-environment.md) before any
pymatgen, ASE, or RDKit work. Consult the machine-readable
[provider capability catalog](references/provider-capabilities.json) for exact API signatures,
tested invariants, format/unit/PBC/order boundaries, and per-provider evidence state. Refuse an
unpinned or mismatched provider for activation evidence.

## Validate this candidate

Run the isolated unit suite, the skill validator, and both candidate validation levels. Inspect
the generated JSON reports after each command. Follow [fixture-manifest.json](references/fixture-manifest.json)
for fixture identity and [validation-state.json](references/validation-state.json) for the latest
machine-readable local result and unresolved repository gates. Activation additionally requires
real artifacts, pinned backend integration,
shared-contract adapters, expert review, registry promotion, and fresh cross-skill tests; local
candidate success alone cannot satisfy those conditions.
