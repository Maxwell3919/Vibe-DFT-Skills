---
name: dft-structure-preparation
description: Audit and prepare traceable periodic or molecular structures with deterministic identity, atom mapping, cell/supercell/strain and lattice-axis slab construction, bounded coherent-interface matching, explicit interstitial/defect/substitution edits, adsorbate or host-guest placement, collision gates, round-trip classification, and DFT export planning. Use when a CIF-derived normalized structure must be transformed or combined without losing parent-child lineage or inventing stability. This remains a non-routable development Skill.
---

# DFT Structure Preparation

Read [the local official-manual cache route](references/manual-cache-route.md) before relying on external structure-library documentation bodies.

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

- Use `import-cif-manifest` to validate and adapt an active
  `structure-manifest@1.0` without silently dropping occupancy or identity evidence.
- Use `audit` for identity, periodicity, coordinate, occupancy, symmetry, charge, and spin gates.
- Use `roundtrip` to distinguish exact representation, periodic equivalence, and loss.
- Use `transform` for `wrap`, `reorder`, general integer `supercell`, or bounded Cartesian
  `strain`.
- Use `make-slab` for a lattice-vector-aligned cleave with explicit layer repeat and vacuum.
- Use `build-interface` to search bounded in-plane repeat pairs and construct one coherent
  interface from two already oriented slabs.
- Use `site-edit` for one explicit interstitial insertion, removal, or substitution.
- Use `place-guest` for explicit adsorbate or periodic host-guest placement.
- Use `plan-export` to create a non-executed QE/VASP/CP2K/SIESTA structure handoff plan.
- Use `probe-backends` to inspect distribution metadata without importing or executing a backend.

Read [workflow.md](references/workflow.md) before transforming data. Read
[data-contracts.md](references/data-contracts.md) before adapting shared repository records.
Read [fail-closed-contract.md](references/fail-closed-contract.md) whenever a gate or dependency
is unresolved. For mechanical routing, parse the machine-readable
[decision table](references/weak-model-decision-table.json) and never take an action stronger than
its `minimum_next_action`.

For provider-facing work, read
[practical-provider-recipes.md](references/practical-provider-recipes.md). It gives
official-manual-backed ASE, pymatgen, spglib, and RDKit calls; explicit unit, mapping, and DFT
handoff checks; and separately labeled operational heuristics. Those recipes remain planning and
review guidance until the named provider route has native fixtures and promotion evidence.
Spglib is reference-only here, not an independently registered provider or activation route.

## Execute the low-reasoning workflow

1. Inventory inputs. Record only a content-derived source label, raw-byte SHA-256, and byte count;
   never expose a user filename or absolute path in an artifact.
2. Import an active CIF manifest or normalize another upstream source into
   [the candidate input schema](schemas/structure-preparation-input.schema.json). Do not call a
   candidate-local envelope a shared `structure-snapshot@1.0` record.

   ```bash
   python3 scripts/structure_prepare.py import-cif-manifest \
     STRUCTURE-MANIFEST.json --out IMPORT.json
   ```

   Use `IMPORT.json.child` as the immutable parent for later commands. Refuse `BLOCK`, prior
   transformations, missing identity preimages, hash/payload disagreement, partial occupancy, or
   disorder rather than adapting a representative model as if it were lossless.
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
   python3 scripts/structure_prepare.py transform INPUT.json --operation supercell \
     --matrix 1 1 0 0 2 0 0 0 1 --out GENERAL-SUPERCELL.json
   python3 scripts/structure_prepare.py make-slab INPUT.json \
     --axis 2 --layers 4 --vacuum-ang 15 --out SLAB.json
   python3 scripts/structure_prepare.py build-interface SUBSTRATE.json FILM.json \
     --max-repeat 6 --max-strain 0.05 --max-angle-deg 1 \
     --gap-ang 2.5 --vacuum-ang 18 --out INTERFACE.json
   python3 scripts/structure_prepare.py site-edit INPUT.json --operation insert \
     --site-id Li-interstitial-0 --element Li --fractional 0.5 0.5 0.5 \
     --out INTERSTITIAL.json
   python3 scripts/structure_prepare.py place-guest SLAB-INPUT.json MOLECULE.json \
     --mode adsorbate --anchor-site O-0 --surface-frac 0.5 0.5 \
     --height-ang 2.2 --out ADSORBATE.json
   ```

6. Verify every parent identity, complete `site_mapping`, created/removed relations, image or
   replica shifts, explicit construction parameters, minimum-distance result, occupancy findings,
   and round-trip classification. Treat every cell-, composition-, interface-, or placement-changing
   operation as a derived structure, never an equivalent round-trip.
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
- Invalidate symmetry after cell, slab, interface, site, or placement mutation until a pinned
  backend recomputes it.
- Enforce determinant, derived-atom, strain, repeat, angle, vacuum, gap, and minimum-distance
  budgets before certifying a derived candidate.
- Reset charge/spin claims after a composition edit unless the operation has exact charge
  arithmetic; never infer charge compensation, oxidation state, or magnetic order.
- Require two already oriented slabs for native interface matching. Treat its minimum-strain
  selection as geometric ranking, never a stable-interface claim.
- Require an explicit coordinate for native interstitials and an explicit anchor, position, and
  orientation for guests. Do not describe either as a site search.
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
or that the modeled chemistry is correct. Likewise, minimum strain, a passed collision gate, or
successful construction does not establish a stable interface, interstitial, defect, adsorbate,
or host-guest configuration. While this directory is in development and non-routable, the current
ceiling is always `no_positive_claim`; `future_gate_ceiling=input_gates_only` describes only a
possible post-promotion local gate and never upgrades the current claim.

Consult [task-profiles-and-maturity.md](references/task-profiles-and-maturity.md) before quoting a
maturity level. Consult [finding-catalog.md](references/finding-catalog.md) before suppressing or
reclassifying a finding. Do not raise a task above its weakest evidence axis.

## Respect backend and license boundaries

Run `probe-backends` only as a metadata probe. A detected distribution is not an imported module,
a successful operation, a license decision, or integration evidence. Read
[official-sources-and-environment.md](references/official-sources-and-environment.md) before any
pymatgen, ASE, spglib, or RDKit work. Consult the machine-readable
[provider capability catalog](references/provider-capabilities.json) for exact API signatures,
tested invariants, format/unit/PBC/order boundaries, and per-provider evidence state. Refuse an
unpinned or mismatched provider for activation evidence. Spglib is currently documentation-backed
only, is not an executable catalog route, and cannot supply activation evidence unless a future
reviewed change first registers it.

## Validate this candidate

Run the isolated unit suite, the skill validator, and both candidate validation levels. Inspect
the generated JSON reports after each command. Follow [fixture-manifest.json](references/fixture-manifest.json)
for fixture identity and [validation-state.json](references/validation-state.json) for the latest
machine-readable local result and unresolved repository gates. Activation additionally requires
real artifacts, pinned backend integration,
shared-contract adapters, expert review, registry promotion, and fresh cross-skill tests; local
candidate success alone cannot satisfy those conditions.
