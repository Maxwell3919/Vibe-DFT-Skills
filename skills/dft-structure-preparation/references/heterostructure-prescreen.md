# Candidate heterostructure prescreen

## Scope and claim boundary

`candidate-heterostructure-prescreen@1.0` is a candidate-local evidence contract for reducing
duplicated structure preparation before a downstream stability workflow. The development
contract establishes no positive claim. `geometric_eligibility_only` is only the maximum local
gate claim a separately reviewed promotion could authorize in the future. Every record fixes:

- `implementation_state=design-only`;
- `semantic_validator_state=not-implemented`;
- `operational_use_authorized=false`;
- `claim_ceiling=no_positive_claim`;
- `future_claim_ceiling=geometric_eligibility_only`;
- `stability_assessed=false`;
- `energy_model_used=false`;
- `execution_authorized=false`;
- `promotion_authorized=false`.

The contract is not a stability predictor, an energy-ranking model, an activation interface, or
a DFT execution request. Schema validity does not establish geometric eligibility. Until a
deterministic semantic validator exists and promotion is separately reviewed, no record may be
used to accept, reject, select, materialize, queue, or calculate a real candidate.

Every record carries these fixed blockers:

- `HETEROSTRUCTURE_PRESCREEN_DESIGN_ONLY`;
- `SEMANTIC_VALIDATOR_NOT_IMPLEMENTED`;
- `OPERATIONAL_USE_NOT_AUTHORIZED`;
- `SCHEMA_VALIDITY_IS_NOT_GEOMETRIC_VALIDITY`.

Removing or renaming a blocker makes the record invalid. A future geometrically eligible
candidate could still reconstruct, dissociate, change registry, or be energetically and
dynamically unstable after calculation.

## Intended future preprocessing reduction

The intended promoted workflow would perform the expensive, structure-rich audit once for each
immutable parent snapshot. The design binds a readable audit artifact reference and exact hash
to the source snapshot, structure manifest, embedded cache preimage, cache-preimage reference,
cache-preimage hash, cache key, and fixed bottom/top layer role. Reuse would be allowed only
after a semantic validator recomputes those relations and confirms that every bound hash and
the prescreen policy hash remains unchanged.

Represent each derived interface initially as a `lightweight-derived-child` receipt. A receipt
contains parent references, the commensurate-cell candidate, registry shift, role-partition
hashes, readable transformation and site-mapping artifact references plus exact hashes, the gate
evaluation hash, four independent workflow states, and explicit geometric-gate evidence. It is
not a replacement for a child structure snapshot. A promoted implementation would materialize a
full child only after it is retained for a downstream lane. Hash drift, unavailable parent
evidence, or required revalidation must block reuse rather than cause a silent rich audit skip.

If implemented and independently validated, this arrangement could remove repeated parsing,
symmetry/occupancy review, and other invariant parent checks from every registry child. It would
not remove child-specific overlap, vacuum, strain, mapping, atom-count, or materialization
checks.

## Two independent future lanes

| Lane | Future post-promotion use | Required registry scope | Forbidden inference |
|---|---|---|---|
| Mechanism preview | Choose an optional geometrically eligible subset for preview or queue ordering | One or more role-aware registries may be chosen, including a single representative | The preview cannot hard-reject another registry, remove a stability-lane candidate, or establish stability |
| Stability | Generate downstream evidence under one consistent method | All geometrically eligible, role-aware unique registries in the declared coverage scope | Geometry alone cannot establish stability; consistent relaxation and common refined-static ranking remain required |

The current design contract authorizes neither lane to route or execute anything. Its lane fields
only make future intent reviewable. Any later calculation needs a promoted operational producer,
an approved request, method contract, provenance, convergence gates, and scientific acceptance
decision.

Do not collapse the lanes into one scalar score. Explicit geometric gates may block a candidate,
and an explicit Pareto vector may help order retained candidates, but `aggregate_score_used` must
remain false. A result from one registry is never a hard-rejection basis for other role-aware
unique registries.

## Commensurate-cell coverage

The intended search family is general two-dimensional commensuration:

1. enumerate bounded 2D Hermite normal form (HNF) supercells for both roles;
2. enumerate bounded unimodular in-plane basis changes;
3. retain the full 2x2 deformation gradient and Green-Lagrange strain for each role;
4. record both principal strains and the maximum absolute principal strain;
5. split deformation between the two roles with an explicit shared minimax objective;
6. apply atom-count and principal-strain gates without an aggregate score;
7. preserve nondominated candidates with their explicit metric-vector basis.

The present development contract deliberately allows each coverage axis and the overall search
to be `not_implemented`, `partial`, or `complete`. These values describe enumeration coverage,
not scientific quality:

- `not_implemented` requires zero enumerated candidates and names excluded space;
- `partial` requires a bounded search declaration and an explicit excluded-space list;
- `complete` means complete only inside the recorded determinant, unimodular-entry, atom-count,
  and strain bounds. Complete coverage may legitimately have zero survivors.

Every emitted commensurate candidate must nevertheless carry both HNF matrices, both unimodular
matrices, the common interface basis, and the full role-specific deformation evidence. A
diagonal-repeat-only implementation therefore reports `partial`; it cannot rename itself as a
general 2D search.

Each candidate records five explicit `gate_evaluations`: atom budget, principal strain, cell
angle, interlayer overlap, and vacuum. Every evaluation carries its criterion-specific
comparator/unit, observed value, threshold, outcome, finding ID when blocked, and an evidence
hash. A gate pass requires all five serialized outcomes to pass. This is still only serialized
evidence until the absent semantic validator recomputes it.

Pareto state carries the actual ordered metric vector, directions and units, a comparison-policy
hash, comparison-universe hash, and universe size. The vector contains maximum absolute
principal strain, total interface atoms, interface area, and cell condition number. No scalar
aggregate is permitted.

## Role-aware registry equivalence

Registry deduplication must preserve the bottom/top partition. The equivalence record fixes
`method=role-aware-periodic-geometry-equivalence` and `layer_roles_preserved=true`. Each class
binds its representative and members to separate bottom- and top-role membership hashes plus an
equivalence-evidence hash.

The declared registry scope also records an enumeration-policy reference/version/hash, registry
set preimage and ID-set hashes, translation domain, vertical-ordering and layer-flip policies,
initial-gap policy hash, matcher name/version/configuration hash, matcher tolerances, periodic
axes, combined configuration hash, counts, and excluded space. `partial` and `not_implemented`
must name at least one excluded region. `complete` may contain zero nominal registries when the
complete upstream commensurate search has zero survivors.

An atom-only geometry match that permits atoms to cross the layer-role partition is insufficient.
Likewise, one representative proves only redundancy within its declared role-aware equivalence
class. It does not make a single registry complete for the stability lane.

## Orthogonal states

Keep these axes separate at both record and child-receipt level:

| Axis | Question answered |
|---|---|
| Coverage | How much of the declared enumeration space was actually implemented and searched? |
| Gate | Did the available candidate evidence pass the explicit geometric criteria? |
| Selection | Was a passing candidate routed to preview, stability, both, or neither? |
| Materialization | Was a full derived structure requested and successfully created? |

No axis implies another. For example, a gate can pass under partial coverage; a selected child
can remain unmaterialized; and complete materialization says nothing about stability. Do not add
an overall `status` that obscures these distinctions.

## Fail-closed handling

Block or downgrade coverage when any required bound, matrix, role assignment, deformation
metric, cache identity, site mapping, or equivalence proof is missing. A hard rejection must name
an explicit geometric criterion and observed/threshold values. The allowed criterion families
are atom budget, principal strain, cell angle, interlayer overlap, and vacuum.

Do not place predicted energies, learned scores, relaxed energies, or stability labels in this
record. Store later calculation evidence in the appropriate calculation and postprocessing
contracts, retain every input/method identity, and let a separate scientific review determine
stability.

## Mandatory semantic-validator blockers

JSON Schema can enforce shape, constants, criterion/unit pairings, non-empty partial coverage,
and several local state implications. It cannot prove matrix algebra, hashes, arithmetic
aggregates, or set equality. The fixed `semantic_validator_obligations` therefore keep
operational use blocked until a deterministic implementation can:

1. recompute HNF canonical conditions, positive determinants, and unimodular determinants;
2. recompute full deformation gradients, strain tensors, principal strains, and shared objective;
3. recompute every gate bound, comparator, observed value, evidence hash, and outcome;
4. verify parent/child artifact bytes, cache preimages, transformations, mappings, and hashes;
5. verify unique IDs, all references, role memberships, and role hashes;
6. verify enumeration, evaluation, eligibility, registry, selection, and materialization counts;
7. recompute Pareto vectors, comparison policy, universe membership, and dominance state;
8. verify role-aware equivalence classes and exact stability-lane coverage of every eligible
   unique class;
9. verify materialization and selection set equalities and record/receipt aggregate states.

The schema intentionally carries these obligations as immutable blocker IDs rather than
pretending that a successful JSON Schema check fulfilled them.
