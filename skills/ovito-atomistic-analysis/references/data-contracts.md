# Candidate and shared-contract boundary

## Candidate schemas

- `schemas/ovito-trajectory-inventory-candidate.schema.json` describes parser-only XYZ/extxyz
  inventory evidence.
- `schemas/ovito-pipeline-spec-candidate.schema.json` describes the non-routable local plan input.
- `schemas/ovito-output-envelope.schema.json` describes common output identity, status, claim, and
  provenance fields.

The output schema includes the dedicated `ovito-candidate-error` stderr envelope; blocked and
internal-error exits therefore retain the same lifecycle and provenance fields as normal reports.

The CLI adds semantic checks beyond schema shape: duplicate keys, source hashes, frame ranges,
operation/provider compatibility, exact parameter sets, evidence roles, cell/PBC consistency,
atom-order and property-schema continuity, deep inventory reductions, source/inventory/spec hash
binding, computed-frame inventory cross-checks, invocation-scoped authorization, distribution
identity, and imported version.

The canonical `references/weak-model-decision-table.json` is a projection of shared
`candidate-decision-table@1.0`: first match by priorities `1..N`, with a final evidence-free
fail-closed default. It cannot authorize an OVITO import, execution, entitlement, or promotion.

## Shared inputs

An activation adapter should consume `atomistic-trajectory-manifest@1.0` and resolve every file,
frame index, topology/site order, PBC, cell mode, time axis, segment, and continuity reference by
exact hash. It should consume `structure-snapshot@1.0` for stable topology and site identity.

The candidate XYZ inventory is not a substitute for either shared contract. XYZ ordinal order
does not establish shared `site_order` identity.

## Planned pipeline interface

The repository's `ovito-pipeline-spec@1.0` remains planned and has no active schema. The local
contract therefore uses the distinct name `ovito-pipeline-spec-candidate` and version `0.1`.
Do not publish it under the shared interface name.

Before activation, freeze a shared schema that preserves:

- source trajectory and structure record references with raw-byte hashes;
- provider edition, version, entitlement evidence class, and operation-specific maturity route;
- frame/time selection, selectors, topology/atom mapping, PBC/cell and unit conventions;
- ordered modifiers with typed parameters and random seeds where relevant;
- requested data, image, and animation artifacts;
- execution authorization receipt distinct from license entitlement;
- artifact hashes, render settings, camera, colors, dimensions, frame rate, and codec;
- validation summaries, limitations, claim ceiling, and human decision.

All current candidate reports use `claim_ceiling=no_positive_claim`,
`promotion_authorized=false`, and lifecycle `execution_authorized=false`. A separately recorded
CLI authorization receipt proves only that one exact source/spec/provider/frame/operation scope
was approved for invocation. `future_gate_ceiling` preserves potential maturity without upgrading
the non-active route.

## Artifact handoff

An eventual adapter may produce `artifact-manifest@1.0` only after output files exist and raw-byte
hashes, sizes, source lineage, tool/version, command, and technical validation are recorded. A plan
must not create an artifact manifest with placeholder hashes.
