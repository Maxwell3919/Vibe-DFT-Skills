# Classification and lineage

## Retrieval carrier and five disjoint semantic classes

Retrieval evidence is a carrier: it records what bytes or metadata were supplied, their identity, version, hash, source ref, license, and availability. Citation metadata is not paper content and cannot satisfy an extraction gate.

The five semantic classes are:

1. `source-assertion`: a bounded paraphrase from one retrieved source and locator, with `quantity=null`.
2. `quoted-numerical-fact`: a structured value, unit, and reported precision from one retrieved source and locator; source prose is not copied.
3. `inference`: a proposed derivation from named fact IDs with uncertainty and a validation action.
4. `project-choice`: a model/parameter choice with owner, state, impact, and failure consequence; it is neither source content nor validated science.
5. `new-claim-proposal`: a no-positive question tied to named inferences and reciprocal validation-step IDs.

Calculation steps are execution-free test plans, not a sixth knowledge claim. IDs across source, fact, inference, project-choice, new-claim, and step namespaces must be disjoint. A statement cannot be moved between classes merely by renaming a field.

## Lineage direction

`source → fact → inference → new-claim proposal ↔ calculation step` and `project-choice → calculation step` are explicit links. Calculation output may later validate or reject an inference, choice, or proposed claim, but it must not rewrite the original literature plan. Record later results in immutable calculation/evidence records and a new claim map.

## Weak-model rule

When uncertain, classify a statement lower: source metadata rather than fact, proposed inference rather than conclusion, and unverified assumption rather than validated input. Report one missing locator, hash, version, premise, route, or evidence profile as the minimum next action.
