---
name: dft-campaign-efficiency
description: Record, compare, and maintain privacy-safe QE, VASP, CP2K, and SIESTA campaign experience to reduce avoidable wall time, core-hours, storage, reruns, and workflow delay without weakening scientific acceptance. Use when a calculation campaign completes, stops, fails, is abandoned, reaches acceptance, or faces a costly promotion decision; when comparing parallel or workflow configurations; when diagnosing cost and critical paths; and when deciding whether an efficiency lesson is anecdotal, campaign-validated, cross-campaign-validated, or superseded.
---

# DFT Campaign Efficiency

Read [the local official-manual cache route](references/manual-cache-route.md) before using external code documentation to classify an efficiency observation.

Learn only from measured campaign evidence. Preserve the scientific objective and acceptance criteria. Never present project experience as official behavior of any calculation code.

When the campaign belongs to a managed calculation workspace, read [the campaign record and taskbook route](references/calculation-workspace-and-taskbook.md). Keep the private experience store outside the workspace and Git; append only authorized privacy-safe `data` or `report` artifacts. In review mode, record them `pending-review` before a later approval. Taskbook review does not promote evidence grade, transferability, efficiency, or scientific acceptance.

## Start from the case, not a template

Run this workflow when a QE, VASP, CP2K, or SIESTA chain completes, stops, fails, is abandoned, reaches scientific acceptance, or reaches a costly promotion decision. An active stage may support a provisional scheduling decision, but it cannot support an accepted-result claim.

1. Read [references/case-first-learning.md](references/case-first-learning.md).
2. When converting cases into immediate run-control advice, read
   [references/operational-time-savers.md](references/operational-time-savers.md).
3. Inventory actual state from scheduler metadata, output markers, required artifacts, and downstream validation. Do not infer state from a directory name, README, job name, or `JOB DONE` alone.
4. Write a free-form case narrative in the authorized private project location. Keep only the minimal evidence kernel structured; do not force a chapter layout before repeated cases reveal one.
5. Separate observed facts, official software behavior, inherited project practice, and current analysis.
6. Record costs, missing metrics, failures, recoveries, scientific gates, decision lineage, and counterfactual estimates. Label estimates as estimates.
7. Compare only evidence that passes [references/comparability-and-evidence.md](references/comparability-and-evidence.md).
8. Emit a bounded lesson, a pilot proposal, or `No new transferable experience`.

Use a valid immutable pre-decision `run_manifest.json` when one exists, but do not discard older or failed campaigns solely because they predate the manifest contract. A completed unreviewed run may preserve measured cost, but it cannot validate a recommendation. Normalize a narrative into the JSON/SQLite store only after its meaning is stable.

## Keep state gates separate

Classify each stage independently:

- `software_finished`: the executable ended normally;
- `artifact_complete`: every required output exists and is readable;
- `numerically_valid`: convergence, closure, and consistency checks pass;
- `physically_valid`: the result passes task-specific physical checks;
- `postprocess_valid`: parsing, transformations, and derived quantities are valid;
- `scientifically_accepted`: the declared observable and uncertainty gates pass;
- `promotion_eligible`: the next stage is justified by the evidence and budget.

Never collapse these states into one completion flag. A stage may be software-finished and still be artifact-incomplete or scientifically rejected.

## Keep evidence classes isolated

- The corresponding code's official documentation controls syntax, defaults, prerequisites, and program behavior.
- Campaign records contain measured project evidence only.
- Recommendations are current analysis derived from cited record ids.
- If experience conflicts with official behavior, correct or supersede the experience record.
- Never write campaign records into a calculation skill's official-reference directory.

## Collect the complete cost path

Record when available:

- code/build, task type, anonymized system class, atom count, protocol id, and configuration id;
- numerical/parallel configuration needed to assess transferability;
- wall time, core-hours, queue wait, memory, storage, restarts, SCF/ionic iterations, repeated work, and human workflow delay;
- scientific acceptance, accuracy metrics, stop/failure code, and evidence checksum;
- critical-path classification: compute, scheduler, I/O, memory, load balance, convergence, dependency, or human workflow.

Do not count relaxed tolerances, omitted q points, incomplete downstream stages, or unconverged outputs as efficiency improvements.

For phonon, EPC, or superconducting-Tc campaigns, also read [references/phonon-tc-efficiency.md](references/phonon-tc-efficiency.md). Treat q-grid convergence, electronic k-grid convergence, integration/smearing convergence, Tc-solver convergence, and model uncertainty as independent gates.

## Normalize only when useful

The private store is an optional normalization layer, not the source narrative. Initialize and ingest it outside the repository when the current schema represents the case without erasing stage lineage or uncertainty:

```bash
python3 scripts/dft_efficiency_cli.py from-run run_manifest.json \
  --system-class <ANONYMIZED_CLASS> --atom-count <N> \
  --configuration-id <CONFIGURATION_ID> --out campaign_record.json
python3 scripts/dft_efficiency_cli.py init --db <PRIVATE_DB>
python3 scripts/dft_efficiency_cli.py ingest --db <PRIVATE_DB> campaign_record.json
python3 scripts/dft_efficiency_cli.py recommend --db <PRIVATE_DB> \
  --code qe --code-version <VERSION> --task-type <TASK> \
  --system-class <ANONYMIZED_CLASS> --atom-count <N> \
  --protocol-id <PROTOCOL_ID> --out recommendation_record.json
```

The tool rejects private identifier keys and nonconforming records. It records completed-unreviewed, failed, and stopped costs. Accepted/rejected ingestion and positive recommendations remain fail-closed until a platform trust resolver authenticates the hash-linked calculation → human decision → post-decision claim chain; a self-filled hash or boolean is never sufficient. Do not commit the database; `.gitignore` excludes runtime databases and `state/`.

If the schema cannot represent a case faithfully, retain the private narrative, record the schema gap, and propose a versioned migration. Do not distort the case to satisfy the current schema.

## Grade experience

Use [references/experience-lifecycle.md](references/experience-lifecycle.md):

- `anecdotal`: one observation; no recommendation;
- `validated-for-this-campaign`: repeated comparable evidence within a campaign/protocol;
- `cross-campaign-validated`: independent comparable campaigns support the scope;
- `superseded`: new evidence or version changes invalidate the prior rule;
- `insufficient-evidence`: no safe comparison is available.

Preserve counterexamples and revision history. Never silently rewrite a rule to remove contrary evidence.

## Recommend conservatively

- Require scientifically accepted records under the same protocol for a positive speed/accuracy recommendation.
- Failed or rejected records may support bounded failure-avoidance gates, but never prove a faster accepted route.
- Require repeated accepted observations per compared configuration before claiming a stable savings fraction.
- Compare median core-hours and wall time; disclose both.
- Recommend one bounded change or pilot test at a time.
- Cite all evidence record ids, applicability keys, savings estimate, confidence, scientific gate, and limitations.
- Keep the result advisory; the corresponding calculation skill decides and validates actual input changes.

## Report without fixing chapters

Write the answer in the order that makes the case easiest to understand. It must still make the evidence inventory, missing metrics, comparability decision, measured versus estimated costs, recommendation status, scientific risk, validation gate, and record update discoverable. Do not add empty sections merely to satisfy a template.
