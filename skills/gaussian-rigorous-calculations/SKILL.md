---
name: gaussian-rigorous-calculations
description: Design and audit fail-closed Gaussian 16 molecular electronic-structure calculations with explicit revision, licensed-environment, model-chemistry, charge/multiplicity, checkpoint-lineage, termination, optimization, and frequency evidence. Use for Gaussian input planning, offline input or log inspection, restart provenance, and deciding what a Gaussian result can support; this development Skill never launches Gaussian or treats natural-language claims as evidence.
---

# Gaussian rigorous calculations

This Skill is **in development and non-routable**. It provides a deterministic offline
planning and audit layer, but it does not activate Gaussian, run a licensed binary,
or issue a positive scientific claim. Preserve `claim_ceiling=no_positive_claim`
until the repository promotion delta and private real-artifact validation are
independently accepted.

## Read before acting

1. Read [the fail-closed contract](references/fail-closed-contract.md).
2. Read [the task evidence profiles](references/task-evidence-profiles.json).
3. Read [the official-source boundary](references/official-sources.md).
4. Read [the environment and license boundary](references/environment-and-license.md).
5. Read [the parser boundary](references/parser-boundary.md) before interpreting a
   parser pass.
6. Read [the weak-model decision table](references/weak-model-decision-table.json)
   as `candidate-decision-table@1.0` when selecting the next state or action. Evaluate
   strictly increasing `priority` and stop at the first match; never merge multiple
   rows into a broader permission. If no earlier row matches uniquely, select the
   final `default_case_id`. The table cannot authorize execution or promotion.
7. For provider-feature discovery, read the machine-readable
   [feature catalog](references/feature-catalog.json), then resolve every cited
   first-party source. A catalog entry is documentation evidence, not guard or native
   support.
8. For a real-platform handoff, read
   [calling and recipe boundary](references/calling-and-recipes.md) and select exactly
   one entry from [task recipes](references/task-recipes.json). Every provider recipe
   is `execution_authorized=false` and `native-not-run` in this development state.

Do not substitute model memory, a user statement, a GaussView screenshot, a smooth
curve, or an unbound checkpoint for those records.

## Manual-first discovery contract

Resolve requests in this order:

1. Match the exact feature or task in `feature-catalog.json`.
2. Resolve all `source_ids` against public first-party Gaussian pages and the exact
   revision boundary. If a decisive detail is missing, return it as unresolved.
3. Read the selected task recipe's preconditions, input/output contract, failure and
   restart semantics, and scientific gates.
4. Check `guard_support` separately. `guard-not-supported` blocks the local guard even
   when Gaussian publicly documents the provider feature.
5. Check `native_validation`. On this host it is `native-not-run`; do not report any
   provider command, import, conversion, or calculation as tested.

The documented Unix entry points are `g16 job-name` and a `g16` process with audited
stdin/stdout bindings. The public utilities include `formchk` and `cubegen`. This
Skill records those real interfaces so a licensed adapter can be reviewed; it does
not call them and does not assume an undocumented `g16 --version` flag.

## Non-negotiable boundary

- Never execute `g16`, `formchk`, `cubegen`, a scheduler, a shell command, or a remote
  command.
- Never request or expose licensed manuals, binaries, checkpoint contents, or private
  calculation data. Store only safe labels, sizes, hashes, and bounded derived facts.
- Treat Gaussian 16 revision, platform, license authorization, input bytes, output
  bytes, and checkpoint ancestry as separate evidence.
- Do not infer method, basis, charge, multiplicity, task completion, stationary-point
  type, or scientific acceptance from a filename or prose.
- Block multi-step `--Link1--`, ONIOM, External, Counterpoise, `Gen`/`GenECP`,
  periodic, excited-state, solvent, IRC, scan, NMR, composite, and post-HF claims
  until a dedicated task profile and real licensed fixture exist.
- The only registered model-chemistry parser profile is synthetic
  `B3LYP/6-31G(d)`. Any other method/basis blocks at planning time until public-source
  and licensed real-fixture evidence extend the profile.
- Plain `Opt Freq` supports only a minimum candidate. Transition-state optimization
  remains blocked; `frequency` may count modes for an externally supplied
  transition-state candidate.
- A normal termination is only a technical completion signal. It does not establish
  basis convergence, method adequacy, conformer/global-minimum identity, thermochemical
  validity, experimental agreement, or scientific acceptance.

## Low-reasoning workflow

Follow the numbered order. Do not skip a failed or missing gate.

### 1. Classify the request

Choose exactly one supported candidate task:

- `single_point`
- `optimization`
- `frequency`
- `optimization_frequency`

If the requested terminal task is outside this set, return `local_gate_blocked` and
name the unsupported task. Do not quietly reduce it to a single point.

### 2. Freeze a plan

Create a request JSON containing the exact revision, method, basis, charge,
multiplicity, atom count, target observable/unit/tolerance, stationary-point intent,
accepted molecular-structure manifest hash, checkpoint label, and optional
parent-checkpoint hash. Then run:

```bash
python3 -B skills/gaussian-rigorous-calculations/scripts/gaussian_guard.py \
  plan --request request.json --out plan.json
```

An unspecified version, method, basis, charge, multiplicity, atom count, observable,
unit, or tolerance blocks the plan. `plan` never fills a scientific default.

### 3. Audit the input bytes

```bash
python3 -B skills/gaussian-rigorous-calculations/scripts/gaussian_guard.py \
  audit-input --input case.gjf --plan plan.json --out input-audit.json
```

Require all of the following:

- exact input SHA-256 and byte count;
- one supported route section and no unsupported feature;
- exact method/basis and task match to the plan;
- exact charge, multiplicity, and atom-count match;
- canonical element/atomic-number identity plus electron-count/multiplicity parity;
- a portable checkpoint basename matching the plan when checkpoint output is planned;
- a hash-bound parent checkpoint reference whenever `%OldChk`, `Geom=Check`,
  `Guess=Read`, `ChkBasis`, or `ReadFC` is requested.

Exit `0` means only that implemented input gates passed. Exit `2` is blocked or
invalid. Do not turn either result into a scientific verdict.

### 4. Separate execution authorization

This candidate has no execution action. A licensed platform may later consume the
audited plan only after a human/platform authorization record binds the exact input,
revision, host profile, resource request, working directory, and intended side
effects. Absence of that external record means `needs_authorization`; it is not an
invitation to run locally.

### 5. Audit the run bytes

```bash
python3 -B skills/gaussian-rigorous-calculations/scripts/gaussian_guard.py \
  audit-run --input case.gjf --output case.log --plan plan.json \
  --execution-record execution-record.json --out run-audit.json
```

The audit re-runs every input gate and then checks exact output identity, a strict
external record binding the input,
output, plan, environment, authorization and checkpoint metadata, revision,
error/normal termination, final SCF energy presence, known SCF-failure absence, requested optimization
completion, frequency presence, and the planned imaginary-frequency count. The
record is still unsigned metadata until a trusted bundle authenticates its issuer.
The audit does not parse or publish raw molecular orbitals, coefficients, checkpoint
contents, or licensed text.

### 6. Apply task-specific evidence

- `single_point`: input gates, matching revision, one technical normal termination,
  and at least one parsed final SCF energy.
- `optimization`: all single-point gates plus an optimization-completed marker. This
  is not proof of a global minimum.
- `frequency`: all single-point gates plus frequencies and the stationary-point
  rule: a minimum has zero negative frequencies; a transition-state candidate has
  exactly one. Near-zero modes remain a limitation.
- `optimization_frequency`: both optimization and frequency gates from the same
  bound job. Separate jobs require an explicit structure/checkpoint lineage profile,
  which is not implemented here.

The deterministic pass is at most a future technical candidate. While lifecycle is
`development`, the emitted claim ceiling remains `no_positive_claim`.

### 7. Respond in a fixed shape

Return these fields, in this order:

1. `route`: `gaussian-rigorous-calculations`
2. `action_state`: `local_gate_blocked`, `needs_evidence`,
   `needs_authorization`, or `local_gate_passed_limited`
3. `claim_ceiling`: always `no_positive_claim` while in development
4. `passed_gates`
5. `blocking_findings`
6. `smallest_next_action`
7. `evidence_refs`: safe label plus SHA-256 only
8. `limitations`

Use the report's finding codes verbatim. Do not replace a missing record with an
explanation.

## Environment probe

The probe validates only a user/platform attestation document; it never searches for
or runs Gaussian:

```bash
python3 -B skills/gaussian-rigorous-calculations/scripts/gaussian_guard.py \
  probe-environment --attestation gaussian-attestation.json --out environment.json
```

A valid attestation still does not authenticate a license or authorize execution.
The current registered target is Gaussian 16 Rev C.02 on the stated Apple M-series
profile. The public C.02 platform list covers Apple M-series macOS 12-15, while the
recorded current host is macOS 26.5.2; this is an unsupported-current-host blocker,
not evidence that the binary could or could not run.

## Handoff boundary

`molecular-structure-manifest@1.0` is an active input interface.
`quantum-chemistry-run-manifest@1.0` remains planned. Therefore this candidate cannot
produce a live cross-Skill run handoff. A future promotion must add the schema,
production semantic evaluator, exact route actions, private real-artifact tests,
licensed platform adapter, source-tree hash, installer coverage, and weak-model blind
tests atomically.
