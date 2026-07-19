# Fail-closed reporting contract

## Authority

The candidate may read caller-supplied local JSON, derive a plan or audit in memory, and create one new caller-selected JSON file. It may not execute calculations, resolve credentials, fetch sources, authenticate a human, edit evidence, send a response, submit a manuscript, or publish an artifact.

## Ordered gates

| Gate | Pass evidence | Blocking result | Minimum next action |
| --- | --- | --- | --- |
| Strict input | Request/evidence bases retain stable directory identities; every component passes `openat(O_DIRECTORY|O_NOFOLLOW)`, and one final `O_NONBLOCK|O_NOFOLLOW` fd is a bounded single-link regular UTF-8 JSON object whose pre/post/anchored/lexical identity agrees; no BOM, duplicate key, non-finite number, FIFO, base swap, or read race | `REPORT.JSON.INVALID` | Replace the first invalid input or unstable base |
| Privacy | No private path, email, host/account label, or credential-like assignment | `REPORT.PRIVACY.UNSAFE_TEXT` | Anonymize the reported value |
| Claim-map identity | Exact `claim-evidence-map@1.0` ID and raw-byte SHA-256 match the request ref | `REPORT.HASH.MISMATCH` | Recompute the ref from unchanged bytes |
| Claim support | Selected claim is `supported` with nonempty evidence and gate IDs | `REPORT.CLAIM.UNSUPPORTED` | Resolve the claim-map blocker |
| Positive-claim trust | Selected claim level is `no_positive_claim`; candidate-local positive statements are redacted | `REPORT.EXTERNAL_BUNDLE.REQUIRED` | Validate positive claims through an external production bundle |
| Evidence | Every selected evidence ID resolves to a present hashed record or file | `REPORT.EVIDENCE.NOT_PRESENT` | Add exact content-addressed evidence |
| Gates | Every selected gate resolves to `pass` or justified `not-applicable` | `REPORT.GATE.NOT_PASSING` | Resolve the decisive gate |
| Citation | Official-source evidence has a bounded source label and locator | `REPORT.CITATION.LOCATOR_MISSING` | Add page, section, table, or figure locator |
| Coverage | Every selected claim occurs in a section and every artifact ID resolves | `REPORT.SECTION.CLAIM_UNMAPPED` | Map the omitted claim |
| Decision lineage | Accepted/rejected source map has a scientific decision ref | `REPORT.DECISION.LINEAGE_MISSING` | Supply the post-decision map |
| Output | A fresh target is published from a still-open staging fd by no-replace hard link only after fd/name inode, size, and payload-hash agreement; target/source/fd agree after link, the directory is synced before staging cleanup and after final verification, and write/sync/substitution/late-target failures roll back only the installed identity | `REPORT.JSON.INVALID` | Choose a fresh stable output path and resolve the first I/O failure |
| Audit binding | Canonical audit equals the audit recomputed from exact plan bytes | `REPORT.RENDER.AUDIT_MISMATCH` | Re-audit the unchanged plan |
| Release | Production bundle validation and human release are external | `publication_ready=false` | Request external validation and release review |

Stop at the first decisive failure in the weak-model response. Preserve all findings in the JSON artifact; never hide a blocker as a warning.

## Hash and trust rules

- Hash exact raw bytes without JSON reserialization or whitespace normalization.
- Treat a structurally valid ref as unresolved until production bundle semantics resolve it.
- Treat source authority and license as external trust decisions; a citation locator does not prove either.
- Preserve a human acceptance value only from the source claim map. The candidate cannot authenticate the actor or create acceptance.
- A locally clean package remains a draft. `render-package` is not publication.
