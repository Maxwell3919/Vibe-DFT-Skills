# Repository interface manual

Run every command from the `Vibe-DFT-Skills` repository root. This manual distinguishes the local candidate writer from active repository contracts and any future publication system.

## 1. Interface and route status

| Surface | Status | Exact interface | Authority |
|---|---|---|---|
| Report request | candidate-local | `dft-report-request@1.0` object accepted by `reporting_cli.py` | Describes requested sections and exact upstream refs only |
| Claim input | implemented repository contract | `contracts/claim-evidence-map.schema.json` | Supplies bounded claims, evidence IDs, gates, ceilings, and decision lineage |
| Candidate plan/audit/package | candidate-local | `scientific-report-candidate-plan`, `dft-report-candidate-audit`, `scientific-report-candidate-package` | Unsigned draft artifacts; none is an active repository contract |
| Route | development/non-routable | `tools/operation_routes.py route dft-reporting` | Any nonzero exit, null route, or blocked decision stops production handoff |
| Manuscript conversion or publication | not implemented | no adapter | No send, submission, or publication authority exists here |

The active upstream contracts do not activate this Skill. A candidate exit `0` establishes only that the exact local step passed its bounded checks.

## 2. Request and artifact schemas

The request must be one strict UTF-8 JSON object with exactly these top-level fields:

```text
schema_version, contract_name, request_id, report_id, title, language,
generated_utc, claim_map_ref, selected_claim_ids, sections,
citation_locators, artifact_refs, campaign_refs, limitations
```

Require `schema_version=1.0` and `contract_name=dft-report-request`. Bind `claim_map_ref` to the exact raw-byte SHA-256 and `map_id` of the supplied `claim-evidence-map@1.0`. `artifact_refs` and `campaign_refs` are identity declarations only: this CLI checks their shapes but does not resolve or authenticate the referenced files. Resolve them in a production bundle before relying on them.

The command chain writes three new files and refuses overwrite:

| Command | Required inputs | Candidate artifact | Required invariant |
|---|---|---|---|
| `plan` | request plus exact claim-map file | `scientific-report-candidate-plan` | `tool_claim_ceiling=no_positive_claim`, `publication_ready=false` |
| `audit` | unchanged plan bytes | `dft-report-candidate-audit` | subject ref hashes the exact plan bytes; `render_allowed=true` only on pass |
| `render-package` | unchanged plan plus its exact audit | `scientific-report-candidate-package` | `draft_only=true`, `publication_ready=false`, `external_message_sent=false` |

These candidate artifacts have no active JSON Schema registration. Do not label them `scientific-report@1.0`, use them as a publication record, or treat self-declared refs as authenticated evidence.

## 3. Local command and side-effect boundary

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-reporting/scripts/reporting_cli.py plan \
  --request skills/dft-reporting/fixtures/valid-report-request.json \
  --claim-map skills/dft-reporting/fixtures/valid-claim-map.json \
  --out OUTPUT/report-plan.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-reporting/scripts/reporting_cli.py audit \
  --plan OUTPUT/report-plan.json --out OUTPUT/report-audit.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-reporting/scripts/reporting_cli.py render-package \
  --plan OUTPUT/report-plan.json --audit OUTPUT/report-audit.json \
  --out OUTPUT/report-package.json
```

These commands are not dry runs of their local operation: on success each performs one no-overwrite local JSON write. Their summaries therefore distinguish `local_write_performed` from `external_execution_performed`. They never run DFT, contact a scheduler or network service, edit a manuscript, send a message, or publish.

An `execute` request means something different: it is a separately routed action with an immutable `execution-request@1.0`, an exact human decision, and—when side effects require it—a bounded single-use `execution-lease@1.0`. This reporting CLI has no `execute`, `send`, or `publish` subcommand.

## 4. Contract chain and answer contract

Keep the following records separate:

| Contract | Role in this workflow | Candidate authority |
|---|---|---|
| `workflow-plan@1.0` | Optional upstream coordination plan | Consume ref only; do not create here |
| `execution-request@1.0` | Exact calculation/tool execution intent | Not created or authorized here |
| `decision-record@1.0` | Human scientific acceptance or release decision | Preserve exact ref; do not authenticate or invent |
| `execution-lease@1.0` | One bounded side-effect grant | Not issued or consumed here |
| `workflow-event@1.0` | Append-only state observation | Not emitted here; a draft file is not an event |
| `claim-evidence-map@1.0` | Claim, evidence, gate, and ceiling source | Required exact input |
| `agent-action-envelope@1.0` | Structured agent answer | Created outside this CLI and validated separately |

Do not paste the candidate summary into an answer and call it validated. Build an `agent-action-envelope` that cites the exact candidate artifact hash, preserves every blocker and limitation, reports the actual route state, sets authorization and tool-run state explicitly, and names one smallest next action. Validate it with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  tools/validate_agent_answer.py ANSWER_ENVELOPE.json --pretty
```

Exit `0` establishes internal consistency with no trust-bearing positive claim. Exit `3` means external bundle verification is still required. Exit `2` blocks the answer. None authenticates a human decision by itself.

## 5. Evidence and citation handoff

1. Validate the exact claim map with `tools/validate_contract.py claim-evidence-map CLAIM_MAP.json`.
2. Require every selected claim to be `supported`, below or equal to the map ceiling, linked to nonempty present evidence IDs, and linked to passing or not-applicable gate IDs.
3. For an `official-source-record` evidence item, require a bounded citation locator such as page, section, table, or figure. A DOI, URL, title, or locator is metadata, not authentication or paper-content evidence.
4. Hash the exact candidate output bytes and place that ref in a content-addressed bundle. Run `tools/validate_bundle.py` and the repository semantic validators before any positive or trust-bearing handoff.
5. Preserve adverse evidence, missing refs, license limits, and unresolved authority. Never replace them with fluent prose.

## 6. Acceptable synthetic workflow

A candidate-local workflow is acceptable only when all of these checks hold:

1. The route check is recorded and its development/non-routable state is not presented as active.
2. The request and exact claim map pass strict input, privacy, raw-hash, claim, evidence, gate, citation, and coverage checks.
3. `plan -> audit -> render-package` all exit `0`; each output is fresh; the audit binds the exact unchanged plan; the package binds both exact inputs.
4. The package remains draft-only with no publication or message claim.
5. The final agent answer passes `validate_agent_answer.py` at its supported ceiling, or remains blocked with the first decisive finding and smallest next action.

Production reporting remains blocked until the Skill is promoted, the route is active, all referenced artifacts resolve in a verified bundle, and separate human scientific and release decisions are authenticated.
