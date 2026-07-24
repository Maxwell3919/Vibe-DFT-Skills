# QE fail-closed execution contract

## Purpose

Use this contract to keep a weak or inattentive model from turning missing evidence into a positive QE conclusion. The deterministic tool covers a deliberately narrow surface and blocks unsupported claims. It does not launch QE.

## Non-negotiable state machine

| State | Entry evidence | Allowed outcome | Blocking condition |
|---|---|---|---|
| `objective` | anonymous case/protocol, task, QE version, observable, unit, tolerance | create a plan | any required value missing or invented |
| `official_behavior` | exactly one version-matching manual entry | state a documented fact | ambiguous entry, version mismatch, stale live source, or unspecified retrieval mode |
| `input_ready` | plan + `pw.x` input + readable pseudopotentials + hashes + required parent manifest | stage the input for an authorized run | any audit gate not `pass` |
| `execution_complete` | audited input and output from the same version/settings | describe execution as complete | no `JOB DONE.`, fatal marker, SCF/ionic failure, or echoed-setting mismatch |
| `numerically_supported` | unchanged plan plus distinct passing input/output audits and content-bound fixed-protocol series | report stable-tail evidence | plan/hash/value mismatch, reused evidence, unsupported extraction, mixed protocol, too few points, or tolerance violation |
| `scientifically_supported` | all prior states plus claim-specific model/physics checks | make the bounded scientific claim | any unassessed convergence dimension, ancestry, model, or physical check |

Do not skip a state. Missing evidence is `blocked` or `incomplete`, never an invitation to infer a value.

## Resolve the bundled tool

Resolve `QE_SKILL_ROOT` to the directory containing the active `SKILL.md`, then use an absolute script path. Do not assume the calculation directory is the skill directory.

```bash
QE_GUARD="$QE_SKILL_ROOT/scripts/qe_guard.py"
python3 "$QE_GUARD" --help
```

If the active skill path cannot be resolved, stop and report that the deterministic gate was not run.

## 1. Create the objective contract

Do this before designing or auditing a scientific calculation. Do not fabricate a tolerance when the user has not supplied or accepted one.

```bash
python3 "$QE_GUARD" plan \
  --case-id <ANONYMIZED_ID> \
  --protocol-id <PROTOCOL_ID> \
  --task-type <scf|relax|vc-relax|bands|dos|pdos|phonon|epc|neb> \
  --qe-version <VERSION> \
  --objective <OBJECTIVE> \
  --observable <OBSERVABLE> \
  --observable-unit <UNIT> \
  --absolute-tolerance <TOLERANCE> \
  --out qe_plan.json
```

Use `--relative-tolerance` instead of, or in addition to, the absolute tolerance when scientifically appropriate. The generated minimum workflow is a lower bound, not proof that no additional stage is needed.

## 2. Resolve each decisive official entry

For version-sensitive facts with network access:

```bash
python3 "$QE_GUARD" reference \
  --executable pw.x --term ecutwfc --qe-version <VERSION> \
  --live-check --out official_ecutwfc.json
```

For a genuinely offline task, use `--offline`. It returns exit code `3` and `decision: cached_only`; disclose that only the recorded mirror was checked. Omitting both retrieval modes is blocked. Never use `--offline` merely to bypass a failed live comparison.

The reference command may route any executable that maps uniquely to a mirrored `INPUT_*` manual. Only a unique, version-matching entry can support an exact software claim.

Before returning content, the resolver maps the index link to exactly one `official-manifest.json` `sections[]` record. It extracts the generated Markdown's fenced text payload, removes only the wrapper separator newline, recomputes its UTF-8 byte count and SHA-256, and compares both with `sections[].bytes` and `sections[].sha256`. It also requires the exact generated wrapper and rejects traversal, symlink substitution, content outside the closing fence, missing metadata, and any payload mismatch. Require `entry_verification.status: verified`; `blocked_local_entry_integrity` returns exit code `2` and does not return an excerpt.

The default response is bounded to 6,000 Unicode characters. Every verified match reports `total_bytes`, the UTF-8 `returned_range`, full-entry `content_sha256`, `truncated`, `continuation_token`, and `complete_entry_returned`. Every continuation request repeats the manifest/payload/wrapper verification before decoding the content-addressed token. A bounded response that does not contain the complete entry returns exit code `2` with `decision: blocked_partial_entry`; a final continuation page has `truncated: false` but still has `complete_entry_returned: false` because that response alone did not contain the entry prefix. Continue deterministically with the returned token:

```bash
python3 "$QE_GUARD" reference \
  --executable pw.x --term "<TERM>" --qe-version <VERSION> --offline \
  --max-chars 6000 --continuation-token '<TOKEN>'
```

Pages can be concatenated in returned-range order and checked against `content_sha256`. To obtain one response that can support complete-entry review, use `--full-entry`; do not combine it with a continuation token. Large complete entries may produce large JSON output.

## 3. Audit a pw.x input

```bash
python3 "$QE_GUARD" audit \
  --input scf.in \
  --run-dir /runtime/job-working-directory \
  --pseudo-dir /runtime/pseudopotentials \
  --pseudo-manifest pseudo-manifest.json \
  --expected-version <VERSION> \
  --plan qe_plan.json \
  --out qe_input_audit.json
```

For `nscf`, `bands`, or `restart_mode='restart'`, also pass `--parent-manifest`. The parent must bind the same anonymous case, scientific protocol, QE version, and privacy-safe prefix, and must record hashed density/save-directory or restart-checkpoint evidence as appropriate. The report omits runtime directory paths and records content hashes. It checks:

- plain-ASCII input, namelist termination/order, and required namelists;
- `pseudo_dir` and `outdir` resolution from the declared job working directory, without recording those private paths;
- explicit `prefix`, `outdir`, `pseudo_dir`, and `conv_thr` policy fields;
- positive `nat`, `ntyp`, `ecutwfc`, and explicit `ecutrho` plus structural/card counts;
- `ibrav`/lattice parameterization and `CELL_PARAMETERS` consistency;
- explicit coordinate/cell units and `if_pos` values;
- automatic/explicit/Gamma k-point grammar and selected occupation prerequisites;
- SOC/noncollinear consistency;
- pseudopotential containment, nonempty content, format signature, SHA-256, XC metadata consistency, and SOC metadata when required;
- plan, version, and parent-run compatibility.

The pseudopotential manifest is a user-maintained declaration that must predate acceptance of the files. Do not construct it by copying hashes from an unexplained calculation directory and then call that provenance. Its minimum structure is:

```json
{
  "schema_version": "1.0",
  "pseudopotentials": [
    {
      "filename": "Si.upf",
      "sha256": "<64 lowercase hex characters>",
      "source": "<library/release identifier>",
      "source_url": "https://<public source>",
      "xc_functional": "PBE",
      "relativistic": "scalar"
    }
  ]
}
```

The manifest must exactly cover the input pseudopotentials. The guard recomputes each file hash and compares the declared XC and relativistic mode to UPF metadata. This binds identity and a declared source; it does not independently prove the source URL, pseudopotential quality, or suitability for the scientific claim.

The deterministic grammar is intentionally limited to an allowlisted `pw.x` core. Unrecognized/advanced namelists, fields, cards, repeated assignments, and arithmetic coordinate expressions are blocked, not silently ignored. For advanced `pw.x` features and for `ph.x`, `neb.x`, and other programs, use the official lookup and manual workflow and label the input audit `not automated`. That manual record is separate evidence: it cannot replace a failed guard, create a tool pass, or support the `input_ready` state. Extend the deterministic coverage with tests, or retain the blocking state and obtain explicit user acknowledgement before any separately authorized execution.

## 4. Audit the matching output

Run the same command with `--output`:

```bash
python3 "$QE_GUARD" audit \
  --input scf.in --output scf.out --stderr scf.err \
  --run-dir /runtime/job-working-directory \
  --pseudo-dir /runtime/pseudopotentials \
  --pseudo-manifest pseudo-manifest.json \
  --expected-version <VERSION> --plan qe_plan.json \
  --out qe_output_audit.json
```

The automated output gate is limited to `scf`, `relax`, and `vc-relax`. It requires exactly one version banner and one `JOB DONE.`, task-appropriate convergence markers, no fatal/nonconvergence marker, and agreement between echoed `ibrav`, atom/type counts, `ecutwfc`, and `ecutrho` and the audited input. It also requires the separately captured stderr artifact. Signalling IEEE floating-point flags or fatal runtime markers in stderr block `runtime_diagnostics`; other nonempty stderr is surfaced as a warning for case-level review. Other `pw.x` calculation modes are `not automated` for completion even when their input core is parsed. Concatenated runs, a scheduler exit code, omitted stderr, or `JOB DONE.` alone are insufficient.

## 5. Check one convergence dimension

Use a CSV with exactly these columns:

```text
setting,observable,protocol_id,audit_report,input_file,output_file,stderr_file
```

Paths may be absolute or relative to the CSV. Every row must use the same protocol and point to a distinct `qe_guard audit` report created with `--input`, `--output`, and `--stderr`. The underlying files must still exist. The convergence gate recomputes their hashes, binds them to the unchanged `qe_plan.json`, and compares the CSV setting and observable to values extracted by the audit. Copying one audit, input, or output to another setting is blocked; changing stderr after the audit is also blocked.

```bash
python3 "$QE_GUARD" convergence \
  --csv ecutwfc.csv --plan qe_plan.json --protocol-id <PROTOCOL_ID> \
  --parameter ecutwfc --parameter-unit Ry \
  --observable <OBSERVABLE> --observable-unit <UNIT> \
  --direction increasing --absolute-tolerance <TOLERANCE> \
  --tail 3 --out ecutwfc_convergence.json
```

The automated parameter extractors are currently `ecutwfc` (`Ry`), `ecutrho` (`Ry`), `conv_thr` (`Ry`), active-smearing `degauss` (`Ry`), and `k_point_count` (`count`). The automated output observable is currently `total_energy` (`Ry`). Any other name or unit is blocked as unsupported; do not hand-copy an unparsed value to bypass this limitation.

Use `--direction decreasing` when smaller settings are stricter, such as a decreasing threshold. The requested observable, unit, and absolute/relative tolerance must exactly match the plan. A stable tail covers only this observable, dimension, sampled range, protocol, and tolerance. It does not eliminate false plateaus or establish physical validity.

## Exit and report semantics

| Command | Exit | Meaning |
|---|---:|---|
| `plan` | `0` | required objective fields are structurally present |
| `reference` | `0` | unique version match and live source hash match |
| `reference` | `3` | unique version match from cached mirror only; disclosure required |
| `reference` | `2` | includes a partial matched entry, invalid continuation, or another blocking condition |
| `audit` | `0` | every gate requested by that audit invocation passed |
| `convergence` | `0` | the declared stable-tail check passed |
| any | `2` | blocked, invalid, ambiguous, mismatched, or failed |

Read the JSON even after exit `0`. `scientific_claim_decision: blocked` means the command passed only its local scope. Never rewrite a generated report, remove a failing input, or downgrade a finding to obtain exit `0`.

## Execution safety

- Do not launch QE, submit a scheduler job, delete outputs, overwrite a calculation directory, or alter a restart tree unless the user explicitly authorizes that action.
- Stage generated inputs separately from original artifacts and show the exact diff before execution.
- Write reports to new report paths. The guard rejects `--out` when it would overwrite an input, output, plan, manifest, pseudopotential, convergence CSV, or row evidence file.
- Treat private hosts, accounts, absolute paths, raw results, and unpublished identifiers as runtime-only data.
- Keep pseudopotential contents outside reports and source control; record filenames, safe metadata, and hashes only.
- If the tool does not understand a feature, return `not automated` and perform a manual official-document audit. Unsupported never means accepted.
