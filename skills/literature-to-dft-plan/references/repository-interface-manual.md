# Repository interface manual

Run commands from the `Vibe-DFT-Skills` repository root. This candidate consumes supplied metadata and bounded facts offline; it is not a literature search service or a calculation launcher.

## 1. Interface and route status

| Surface | Status | Exact interface | Authority |
|---|---|---|---|
| Literature request | candidate-local | `literature-to-dft-request@1.0` object accepted by `literature_plan_cli.py` | Supplied inventory, classifications, and proposed steps only |
| Source/evidence refs | implemented repository contracts | `official-source-record@1.0`, `evidence-record@1.0` | Shapes for externally resolved evidence; not automatic trust |
| Candidate outputs | candidate-local | `literature-evidence-plan-candidate`, `literature-plan-candidate-audit`, `literature-plan-candidate-package` | Offline draft artifacts; none authorizes a calculation |
| Route | development/non-routable | `tools/operation_routes.py route literature-to-dft-plan` | Any nonzero exit, null route, or blocked decision stops live handoff |
| DOI/publisher retrieval | not implemented | no network adapter | Retrieval, terms, authority, and license checks remain external |

The candidate never claims that it fetched a paper, resolved a DOI, authenticated a publisher, or read source text.

## 2. Request and artifact schemas

The request must be one strict UTF-8 JSON object with exactly these top-level fields:

```text
schema_version, contract_name, request_id, plan_id, generated_utc, objective,
target_observables, sources, facts, inferences, assumptions, new_claims,
calculation_steps, limitations
```

Require `schema_version=1.0` and `contract_name=literature-to-dft-request`. Each source records identity metadata, retrieval status, content hash when resolved, exact source-record ref when available, version, license/redistribution state, and limitations. Do not include article bodies, abstracts copied as evidence, credentials, or private paths.

The candidate writes three fresh artifacts:

| Command | Input | Candidate artifact | Required invariant |
|---|---|---|---|
| `plan` | exact request bytes | `literature-evidence-plan-candidate` | five semantic classes remain separate; `claim_ceiling=no_positive_claim` |
| `audit` | unchanged plan bytes | `literature-plan-candidate-audit` | audit subject ref binds the exact plan hash |
| `render-package` | unchanged plan and exact audit | `literature-plan-candidate-package` | network, authorization, and execution flags remain false |

These names are candidate-local and have no active repository Schema. Do not rename a package to `literature-evidence-plan@1.0` or use it directly as an engine input.

## 3. Local command and side-effect boundary

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/literature-to-dft-plan/scripts/literature_plan_cli.py plan \
  --request skills/literature-to-dft-plan/fixtures/valid-literature-request.json \
  --out OUTPUT/literature-plan.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/literature-to-dft-plan/scripts/literature_plan_cli.py audit \
  --plan OUTPUT/literature-plan.json --out OUTPUT/literature-audit.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/literature-to-dft-plan/scripts/literature_plan_cli.py render-package \
  --plan OUTPUT/literature-plan.json --audit OUTPUT/literature-audit.json \
  --out OUTPUT/literature-package.json
```

Each successful command performs one no-overwrite local JSON write. It is not a dry run of that local write, but it performs no network access, source download, DFT execution, scheduler action, message, or publication. Read `local_write_performed` and `external_execution_performed` independently in the command summary.

Any future network retrieval is a separate `network-read` adapter with explicit terms/license evidence and deterministic failure semantics. Any future calculation is a separate active route with an immutable execution request, human authorization, and lease where required. This candidate implements neither.

## 4. Source and citation evidence

Use this order:

1. Treat DOI, URL, title, author list, journal, year, and abstract metadata as identity metadata only.
2. Treat a source as resolved content evidence only when the supplied record has an exact content hash, bounded locator, retrieval state, source-record ref, applicable version, and license/redistribution state.
3. Classify a paraphrased source assertion separately from a structured quoted numerical fact. A numerical fact requires value, unit, precision/context, source ID, and bounded locator.
4. Record inference premises, uncertainty, and validation action explicitly. Record project choices with owner, status, impact, and failure consequence.
5. Preserve the lineage `source -> fact -> inference -> proposed claim <-> calculation step`; never upgrade a proposal because it resembles a published conclusion.

If an external retrieval implementation is later added, rely on official DOI registration-agency or publisher metadata interface documentation for metadata semantics and version the adapter. That integration is outside this candidate and no online evidence is required for the bundled synthetic fixture.

## 5. Plan, lease, event, and answer handoff

| Contract | Role after human review | Candidate authority |
|---|---|---|
| `workflow-plan@1.0` | Converts selected questions into bounded repository steps | Not emitted here; create through a production planner |
| `execution-request@1.0` | Exact argv/resources/inputs for one approved step | Not emitted or approved here |
| `decision-record@1.0` | Human choice, execution authorization, or scientific decision | Preserve exact ref only |
| `execution-lease@1.0` | Expiring single-use grant for side effects | Not issued or consumed here |
| `workflow-event@1.0` | Append-only observation of later workflow state | Not emitted here; later evidence must not rewrite this plan |
| `run-manifest@1.0` | Terminal calculation handoff | Created only from real run evidence |
| `agent-action-envelope@1.0` | Structured agent answer | Create and validate outside this CLI |

After a human selects a step, check the exact engine Skill route. A development, planned, blocked, null, or nonzero route stops. Translate the step manually through the selected active engine Skill; do not infer parameters absent from the source and project decisions.

Validate the final structured answer with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  tools/validate_agent_answer.py ANSWER_ENVELOPE.json --pretty
```

Exit `0` is internal consistency at no trust-bearing positive claim. Exit `3` still requires external bundle verification. Exit `2` blocks. The answer must carry exact artifact refs, route state, source/evidence limitations, zero execution authority, and one smallest next action.

## 6. Acceptable synthetic workflow

Accept the local workflow only when:

1. every source/fact/inference/project-choice/proposed-claim/step has a unique ID and all links resolve;
2. resolved content has exact hash and locator, version-sensitive sources have versions, and no source body is present;
3. calculation steps name active engine routes in the supplied plan, require completion/convergence/validity evidence, and retain `authorization_required=true`;
4. `plan -> audit -> render-package` exits `0` with fresh outputs and exact hash linkage;
5. the package still states no network access, no calculation authorization, no execution, and `no_positive_claim`;
6. the agent answer validates or reports the first blocker without inventing missing literature or DFT facts.

Passing this candidate does not make its own development route active and does not approve any proposed calculation.
