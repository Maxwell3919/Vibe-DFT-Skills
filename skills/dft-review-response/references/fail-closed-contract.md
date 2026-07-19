# Fail-closed review-response contract

## Scope

The candidate may read supplied local request and claim-map JSON, verify exact-byte linkage, build a point-by-point plan, audit that plan, and create one new local JSON package. It may not edit a manuscript, execute calculations, authenticate people, send messages, submit files, or decide scientific acceptance.

## Ordered gates

| Gate | Pass evidence | Blocking result | Minimum next action |
| --- | --- | --- | --- |
| Strict JSON | Request/evidence bases retain stable directory identities; every component passes `openat(O_DIRECTORY|O_NOFOLLOW)`, and one final `O_NONBLOCK|O_NOFOLLOW` fd is a bounded single-link regular UTF-8 object whose pre/post/anchored/lexical identity agrees; no duplicate key/BOM/NaN/FIFO/base swap/read race | `REVIEW.JSON.INVALID` | Replace the invalid input or unstable base |
| Privacy | Pseudonymous labels and no private path/email/credential text | `REVIEW.PRIVACY.UNSAFE_TEXT` | Anonymize the field |
| Claim-map identity | Exact ID and raw-byte hash match request ref | `REVIEW.HASH.MISMATCH` | Recompute the exact ref |
| Comment coverage | Every comment has exactly one response | `REVIEW.COMMENT.COVERAGE_INVALID` | Add or deduplicate the response |
| Change linkage | Response binds exactly one change or one no-change reason; each change resolves to one matching response/comment | `REVIEW.RESPONSE.CHANGE_LINK_INVALID` | Repair the one-to-one response action |
| Evidence | Scientific/method response and its change bind the same single present hashed evidence | `REVIEW.RESPONSE.EVIDENCE_MISSING` | Supply one exact evidence item |
| Claim | Scientific/method response and change bind the same single supported no-positive claim with passing gates | `REVIEW.CLAIM.UNSUPPORTED` | Resolve the claim map; route positive claims to external bundle validation |
| Change state | Candidate changes remain proposed/not-applicable; completed/implemented is critical and produces no artifact | `REVIEW.CHANGE.IMPLEMENTATION_UNVERIFIED` | Restore proposal state and later produce a changed-artifact record |
| Decision lineage | Accepted/rejected source state has scientific decision ref | `REVIEW.DECISION.LINEAGE_MISSING` | Supply the post-decision claim map |
| Output | A fresh target is published from a still-open staging fd by no-replace hard link only after fd/name inode, size, and payload-hash agreement; post-link target/source/fd identity is checked and directory metadata is synced before staging cleanup and after final verification | `REVIEW.JSON.INVALID` | Choose a fresh stable path and resolve write, sync, substitution, or late-target failure |
| Render binding | Canonical audit equals the audit recomputed from exact passing plan bytes | `REVIEW.RENDER.AUDIT_MISMATCH` | Re-audit the unchanged plan |
| Submission | Human editorial, scientific, privacy, license, and release decisions remain external | `submission_ready=false` | Request reviewed release separately |

## Non-substitution rules

- A response paragraph is not evidence.
- A proposed change is not an implemented manuscript diff.
- A process or calculation exit code is not scientific adequacy.
- A claim-map acceptance string is not authenticated human identity.
- A local render pass is not permission to send or submit.
