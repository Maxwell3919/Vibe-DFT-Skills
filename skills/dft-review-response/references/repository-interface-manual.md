# Repository interface manual

Run commands from the `Vibe-DFT-Skills` repository root. This candidate checks point-by-point lineage and writes a local JSON draft; it does not edit a manuscript or contact a journal.

## 1. Interface and route status

| Surface | Status | Exact interface | Authority |
|---|---|---|---|
| Review request | candidate-local | `dft-review-response-request@1.0` object accepted by `review_response_cli.py` | Supplied pseudonymous comments, draft responses, and proposed changes only |
| Claim input | implemented repository contract | `claim-evidence-map@1.0` | Exact bounded claim/evidence/gate source |
| Candidate outputs | candidate-local | `review-response-candidate-plan`, `review-response-candidate-audit`, `review-response-candidate-package` | No manuscript modification or submission authority |
| Route | development/non-routable | `tools/operation_routes.py route dft-review-response` | Any nonzero exit, null route, or blocked decision stops live handoff |
| Manuscript edit/send/submit | not implemented | no adapter | External side effects remain unavailable |

The planned `review-comment-set@1.0` and `review-evidence-map@1.0` interfaces are not active schemas. Do not present candidate output as either contract.

## 2. Request and artifact schemas

The request is one strict UTF-8 JSON object with exactly these top-level fields:

```text
schema_version, contract_name, request_id, package_id, generated_utc,
manuscript_ref, claim_map_ref, comments, responses, modifications, limitations
```

Require `schema_version=1.0` and `contract_name=dft-review-response-request`. Bind `claim_map_ref` to the exact raw-byte SHA-256 and `map_id` of the supplied `claim-evidence-map@1.0`. `manuscript_ref` is an identity declaration; the CLI does not open, diff, or authenticate the manuscript.

| Command | Required inputs | Candidate artifact | Required invariant |
|---|---|---|---|
| `plan` | request and exact claim map | `review-response-candidate-plan` | reviewer text is replaced by hashes; changes remain proposed/not-applicable |
| `audit` | unchanged plan | `review-response-candidate-audit` | exact plan hash and one-to-one links must pass |
| `render-package` | unchanged plan and exact audit | `review-response-candidate-package` | `draft_only=true`, `manuscript_modified=false`, `submission_ready=false` |

All three are unsigned candidate-local artifacts with no active repository Schema. They cannot prove that a manuscript changed or that a response was sent.

## 3. Local command and side-effect boundary

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-review-response/scripts/review_response_cli.py plan \
  --request skills/dft-review-response/fixtures/valid-review-request.json \
  --claim-map skills/dft-review-response/fixtures/valid-review-claim-map.json \
  --out OUTPUT/response-plan.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-review-response/scripts/review_response_cli.py audit \
  --plan OUTPUT/response-plan.json --out OUTPUT/response-audit.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-review-response/scripts/review_response_cli.py render-package \
  --plan OUTPUT/response-plan.json --audit OUTPUT/response-audit.json \
  --out OUTPUT/response-package.json
```

Each successful command performs one fresh local JSON write; it is not a dry run of that write. Summaries distinguish `local_write_performed` from `external_execution_performed`. The CLI never executes DFT, edits a manuscript, sends email, uploads files, or submits to a journal.

A new-calculation promise is not an execution request. Create a separate bounded workflow plan, choose an active engine Skill, produce an immutable `execution-request@1.0`, obtain an exact human authorization and single-use lease when required, and record later events separately. This candidate cannot perform those steps.

## 4. Point-by-point, evidence, and citation handoff

Require this graph:

```text
one comment -> one response -> one proposed change or one no-change reason
                    |                    |
                    +-- same evidence --+
                    +-- same claim ------+
```

For scientific or method content, require exactly one present hashed evidence item and one supported `no_positive_claim` claim whose gate IDs pass. Positive upstream claims require external bundle verification and remain blocked in the candidate. Preserve defer, disagree, and limitation states rather than converting them to completed changes.

The candidate does not create citation authority. When a response depends on literature, the exact upstream claim map must carry an `official-source-record` evidence ref and bounded locator; source authority, content hash resolution, and license remain production-bundle obligations. A response paragraph and a citation string are not evidence.

## 5. Plan, lease, event, and answer contracts

| Contract | Role | Candidate authority |
|---|---|---|
| `workflow-plan@1.0` | Coordinates any separately approved new calculation or edit workflow | Not created here |
| `execution-request@1.0` | Exact side-effecting tool or calculation intent | Not created or authorized here |
| `decision-record@1.0` | Human scientific, author, privacy, license, or release decision | Preserve exact refs; do not invent/authenticate |
| `execution-lease@1.0` | Bounded single-use side-effect grant | Not issued or consumed here |
| `workflow-event@1.0` | Append-only later calculation/edit/submission observation | Not emitted here |
| `artifact-manifest@1.0` | Exact figure/table/changed-manuscript handoff | Must come from a separate producer |
| `agent-action-envelope@1.0` | Structured agent answer | Create and validate outside this CLI |

Build the final answer from exact artifact hashes, not conversation memory. Preserve route state, blockers, claim ceiling, no-send/no-edit flags, evidence links, and one smallest next action. Validate it with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  tools/validate_agent_answer.py ANSWER_ENVELOPE.json --pretty
```

Exit `0` proves internal consistency only at no trust-bearing positive claim. Exit `3` requires external bundle verification. Exit `2` blocks. An answer envelope never substitutes for an author or release decision.

## 6. Acceptable synthetic workflow

Accept the local workflow only when:

1. the exact claim map validates and its raw-byte hash matches the request;
2. every pseudonymous comment has exactly one response, and every response has exactly one proposed change or an explicit no-change reason;
3. scientific/method response, claim, evidence, and proposed change lineage agree exactly;
4. no change claims `implemented` or `completed`, raw comment text is not copied to generated artifacts, and privacy checks pass;
5. `plan -> audit -> render-package` exits `0` with fresh files and exact unchanged-byte bindings;
6. package flags remain no-edit/no-send/not-ready, and the final agent answer validates or reports the first decisive blocker.

Manuscript editing, changed-artifact verification, human author review, release authorization, and submission remain separate workflows.
