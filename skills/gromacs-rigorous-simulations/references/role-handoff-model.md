# GROMACS role and handoff model

This is a responsibility split, not a set of autonomous permissions. One person or agent may hold several roles, but each handoff stays explicit and content-addressed.

| Role | Reads | Produces | Must not assert |
|---|---|---|---|
| claim planner | scientific request and acceptance policy | no-execution plan request | GROMACS defaults are scientifically sufficient |
| source verifier | exact banner and official pages | version/source decision | a rolling `current` page proves old behavior |
| system-model auditor | coordinates, topology closure, parameters and terms | hash-bound input inventory | missing includes or licenses are harmless |
| protocol auditor | MDP, seed, ensemble, cadence and lineage | local input-gate report | preprocessing or execution occurred |
| execution authorizer | immutable inputs and external authority | future execution lease outside this Skill | this candidate grants permission |
| output/trajectory auditor | exact log, series and frames | completion/statistics/trajectory inventories | completion proves equilibrium or physics |
| scientific reviewer | all inventories plus sensitivity evidence | external bounded decision | a parser pass substitutes for expert judgment |

Handoffs require the prior report's exact raw-byte SHA-256, exact artifact hashes, unresolved findings, current `no_positive_claim`, `report_authenticity=unsigned-candidate-output`, and minimum next action. The self `report_fingerprint` is checked for consistency but is not a trust root. A downstream role cannot delete or downgrade an upstream blocker. Only a separately verified trusted manifest/signature may attest report origin, and independent review is required before promotion.
