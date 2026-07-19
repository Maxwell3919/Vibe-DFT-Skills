# Fail-closed literature planning contract

## Allowed scope

Read supplied local JSON, inventory source metadata and hashes, classify facts/inferences/assumptions, propose calculation steps, audit an unchanged plan, and create one new local JSON draft. Do not browse, download, authenticate, execute, submit, publish, or reproduce source text.

## Ordered gates

| Gate | Pass evidence | Blocking result | Minimum next action |
| --- | --- | --- | --- |
| Strict JSON | Request/evidence bases retain stable directory identities; every component passes `openat(O_DIRECTORY|O_NOFOLLOW)`, and one final `O_NONBLOCK|O_NOFOLLOW` fd is a bounded single-link regular UTF-8 object whose pre/post/anchored/lexical identity agrees; no duplicate key, BOM, non-finite number, FIFO, base swap, or read race | `LIT.JSON.INVALID` | Replace the first invalid file or unstable base |
| Privacy | No private path, email, credential, account, or host data | `LIT.PRIVACY.UNSAFE_TEXT` | Anonymize the field |
| Retrieval | Resolved source has exact content hash and record ref | `LIT.SOURCE.RETRIEVAL_EVIDENCE_MISSING` | Supply exact retrieval evidence |
| Version | Version-sensitive official manual names its version | `LIT.SOURCE.VERSION_MISSING` | Supply a version-matched source |
| License | Source license and redistribution states are explicit | `LIT.SOURCE.LICENSE_INVALID` | Record or conservatively mark the state unknown |
| Fact class | Source assertion is a paraphrase; quoted numerical fact is structured value/unit/precision; both resolve to retrieved content and a locator | `LIT.FACT.NOT_EXTRACTABLE` | Retrieve, classify, and locate exact source evidence |
| Inference | Proposed inference lists existing fact premises and validation action | `LIT.INFERENCE.PREMISE_INVALID` | Bind premise facts |
| Project choice | Project choice has a distinct ID, owner, status, impact, and failure consequence | `LIT.ASSUMPTION.INVALID` | Record the explicit project choice |
| New claim | Proposal remains a no-positive question with inference premises and reciprocal validation-step IDs | `LIT.NEW_CLAIM.OVERCLAIM` | Restore proposed no-positive state and lineage |
| Step | Proposed step tests named inferences and new claims under named choices and observables | `LIT.STEP.LINEAGE_INVALID` | Repair the first unresolved link |
| Route | Step names an active Skill route | `LIT.STEP.ROUTE_NOT_ACTIVE` | Promote or replace the route |
| Authorization | Every calculation step requires separate execution authorization | `LIT.STEP.AUTHORITY_INVALID` | Restore proposed state and authorization requirement |
| Output | A fresh target is published from a still-open staging fd by no-replace hard link only after fd/name inode, size, and payload-hash agreement; post-link target/source/fd identity is checked and directory metadata is synced before staging cleanup and after final verification | `LIT.JSON.INVALID` | Choose a fresh stable path and resolve write, sync, substitution, or late-target failure |
| Render | Canonical audit equals the audit recomputed from exact passing plan bytes | `LIT.RENDER.AUDIT_MISMATCH` | Re-audit the unchanged plan |

## Claim ceiling

The candidate only proves that supplied metadata passed its own classification checks. It does not establish source authority, truth, applicability, numerical adequacy, or scientific acceptance. Keep `claim_ceiling=no_positive_claim` through all commands.
