---
name: dft-campaign-efficiency
description: Record, compare, and maintain privacy-safe QE/VASP campaign experience to reduce avoidable wall time, core-hours, storage, reruns, and workflow delay without weakening scientific acceptance. Use when a calculation campaign completes, stops, fails, is abandoned, or reaches acceptance; when comparing parallel or workflow configurations; when diagnosing cost and critical paths; and when deciding whether an efficiency lesson is anecdotal, campaign-validated, cross-campaign-validated, or superseded.
---

# DFT Campaign Efficiency

Learn only from measured campaign evidence. Preserve the scientific objective and acceptance criteria. Never present project experience as official QE/VASP behavior.

## Trigger on every terminal event

Run this workflow when a QE/VASP chain completes, is intentionally stopped, fails, is abandoned, or reaches scientific acceptance—even when no transferable lesson exists.

1. Obtain a valid `run_manifest.json` from the calculation skill.
2. Read [references/record-schema-and-privacy.md](references/record-schema-and-privacy.md).
3. Collect observed scheduler/runtime metrics and acceptance evidence; mark unavailable metrics explicitly.
4. Build a privacy-safe campaign record and validate it against [campaign-record.schema.json](../../contracts/campaign-record.schema.json).
5. Ingest it into a user-selected private SQLite database outside Git.
6. Compare only records that pass [references/comparability-and-evidence.md](references/comparability-and-evidence.md).
7. Emit an advisory recommendation or `insufficient-evidence` record.

## Keep evidence classes isolated

- Official QE/VASP documentation controls syntax, defaults, prerequisites, and program behavior.
- Campaign records contain measured project evidence only.
- Recommendations are current analysis derived from cited record ids.
- If experience conflicts with official behavior, correct or supersede the experience record.
- Never write campaign records into QE/VASP official-reference directories.

## Collect the complete cost path

Record when available:

- code/build, task type, anonymized system class, atom count, protocol id, and configuration id;
- numerical/parallel configuration needed to assess transferability;
- wall time, core-hours, queue wait, memory, storage, restarts, SCF/ionic iterations, repeated work, and human workflow delay;
- scientific acceptance, accuracy metrics, stop/failure code, and evidence checksum;
- critical-path classification: compute, scheduler, I/O, memory, load balance, convergence, dependency, or human workflow.

Do not count relaxed tolerances, omitted q points, incomplete downstream stages, or unconverged outputs as efficiency improvements.

## Use the private store

Initialize and ingest outside the repository:

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

The tool rejects private identifier keys and nonconforming records. Do not commit the database; `.gitignore` excludes runtime databases and `state/`.

## Grade experience

Use [references/experience-lifecycle.md](references/experience-lifecycle.md):

- `anecdotal`: one observation; no recommendation;
- `validated-for-this-campaign`: repeated comparable evidence within a campaign/protocol;
- `cross-campaign-validated`: independent comparable campaigns support the scope;
- `superseded`: new evidence or version changes invalidate the prior rule;
- `insufficient-evidence`: no safe comparison is available.

Preserve counterexamples and revision history. Never silently rewrite a rule to remove contrary evidence.

## Recommend conservatively

- Require scientifically accepted records under the same protocol.
- Require at least two accepted observations per compared configuration.
- Compare median core-hours and wall time; disclose both.
- Recommend one bounded change or pilot test at a time.
- Cite all evidence record ids, applicability keys, savings estimate, confidence, scientific gate, and limitations.
- Keep the result advisory; QE/VASP calculation skills decide and validate actual input changes.

## Output format

Return:

1. evidence inventory and missing metrics;
2. comparability decision;
3. measured baseline/alternative costs;
4. recommendation status and record ids;
5. scientific risk and validation gate;
6. database update, supersession, or `No new transferable experience`.
