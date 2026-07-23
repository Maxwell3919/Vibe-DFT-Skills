---
name: gpumd-rigorous-simulations
description: Design and fail-closed audit offline GPUMD molecular-dynamics, Green-Kubo/HNEMD thermal-transport, and NEP construction/deployment workflows; inspect run.in/model.xyz/potentials, version and GPU evidence, restart lineage, outputs, trajectories, sampling, uncertainty, and claim support without launching GPUMD.
---

# GPUMD Rigorous Simulations

Keep input syntax, executable identity, GPU compatibility, potential validity, technical completion, ensemble sampling, uncertainty, and scientific acceptance as separate gates. This development Skill never invokes `gpumd`, CUDA, HIP, a scheduler, a shell, or the network.

## Resolve the offline guard

Resolve `GPUMD_SKILL_ROOT` to this candidate directory and use the script in place:

```bash
GPUMD_GUARD="$GPUMD_SKILL_ROOT/scripts/gpumd_guard.py"
python3 "$GPUMD_GUARD" --help
```

Stop if the absolute path cannot be resolved. Do not copy the guard into a calculation directory.

## Follow this low-reasoning workflow

1. Inventory the bounded claim, exact GPUMD release and commit, task, structure, potential, units, three-axis boundary, ensemble, time step, seed, lineage, equilibration, production, observables, uncertainty rule, output cadence, environment, legal status, and execution authorization.
2. Copy [examples/plan-request.json](examples/plan-request.json) and replace only values supported by project evidence. Never invent a seed, potential license, parent state, tolerance, or GPU capability.
3. Run `plan` for the parser-supported NVE/LJ route. Continue to `audit-input`
   only when `decision=pass`. If the result is `incomplete` solely because the
   requested NEP, Green–Kubo, HNEMD, ensemble, or potential is design-only,
   stop the deterministic pipeline and use the task references to produce a
   documentary protocol plus unsupported-gate list. Do not fabricate an NVE/LJ
   request to obtain a pass. Every plan keeps `claim_ceiling=no_positive_claim`.
4. Match GPUMD `5.3` to the pinned tag and commit in [references/official-sources.json](references/official-sources.json). The website's rolling documentation is discovery material, not version-matched proof.
5. Run `audit-input` on `run.in`, `model.xyz`, the potential file, and provenance. The supported core is deliberately limited to one or more MD blocks using `potential`, explicit `velocity` or state velocities, explicit `time_step`, a standard `ensemble`, `dump_thermo`, `dump_restart`, `dump_xyz`, and `run`.
6. Read [references/execution-and-executable-map.md](references/execution-and-executable-map.md). The documented real launch is the no-argument `path/to/gpumd` from an isolated directory containing fixed-name inputs. Do not invent `--version`, `-h`, MPI flags, or input-file arguments. Stop before execution: a future execution Skill must re-check authorization, executable/source/GPU identity, immutable input hashes, resource limits, and output destination.
7. Run `audit-output` on unchanged passing plan/input reports, captured stdout, and `thermo.out`. Completion markers do not establish physics, equilibration, or statistical sufficiency.
8. Run `audit-trajectory` on the exact extxyz named by `dump_xyz`. Check `Time`, `pbc`, `Lattice`, `Properties`, frame/site continuity, and planned cadence.
9. Report all failed, incomplete, unsupported, and not-assessed gates. Because the lifecycle is `development`, current `claim_ceiling` always remains `no_positive_claim`; `future_gate_ceiling` is post-promotion potential only. Every report is explicitly `report_authenticity=unsigned-candidate-output`. Expert scientific review stays external.

## Route to the task content

- For ordinary MD, ensembles, time-step studies, `thermo.out`, trajectory,
  restart, performance, and failure triage, read
  [references/simulation-workflows.md](references/simulation-workflows.md).
- For Green–Kubo EMD or HNEMD conductivity, also read
  [references/thermal-transport-workflows.md](references/thermal-transport-workflows.md).
- For `nep.in`, train/test data, NEP training/restart, model validation, and
  deployment, read
  [references/nep-model-workflow.md](references/nep-model-workflow.md).

Those references distinguish exact v5.3 facts from **operational heuristics**.
Heuristics are project-validation prompts, never GPUMD defaults. The current
guard remains parser-supported only for its NVE/LJ synthetic slice; for other
tasks produce a design and evidence checklist, report `parser_supported=false`,
and do not turn documentary knowledge into a passing audit.

## Create a plan

```bash
python3 "$GPUMD_GUARD" plan --request plan-request.json --out gpumd-plan.json
```

Require anonymous case/protocol IDs, exact `gpumd_version=5.3`, pinned commit, task, objective, claim target, GPUMD's fixed MD unit map, boundary, ensemble, positive `timestep_fs`, independently identified potential, explicit lineage, seed policy, phase boundaries, observable estimators, accepted uncertainty bounds, output cadence, and `execute_external_software=false`.

The supported fixture uses an analytic LJ potential because its format can be checked deterministically. NEP, qNEP, EAM, Tersoff, SW, many-body combinations, training, phonon, Green–Kubo, HNEMD, NEMD, shock, path-integral, and multi-GPU tasks remain design-only until each receives its own official-source profile, parser, fixtures, and tests. Design-only references improve planning but do not increase parser coverage. GPUMD 5.1/5.2 `compute_phonon` results are explicitly outside support because the 5.3 release reports a prior bug fix.

## Audit inputs

```bash
python3 "$GPUMD_GUARD" audit-input \
  --plan gpumd-plan.json --run-in run.in --model model.xyz \
  --potential lj.txt --provenance model-provenance.json \
  --out gpumd-input-audit.json
```

The guard uses a strict command allowlist, rejects ambiguous lines and path-bearing potential names, validates every run block independently, and accounts for GPUMD's non-propagating `ensemble`, `dump_thermo`, `dump_restart`, and `dump_xyz` controls. `time_step` may propagate but must be explicit before the first run.

For `new`, require `model.xyz` without `vel` plus `velocity <K> seed <integer>`. For `state-file-continuation`, require `vel` in the model, no `velocity` command, a parent run ID, state SHA-256, parent final step, and segment start time. `restart.xyz` is a state-file workflow; the guard never calls it an exact integrator continuation because thermostat/barostat internal state and hardware/build reproducibility are not proven.

`model.xyz` must explicitly contain `pbc`, `Lattice`, `Properties=species:S:1:pos:R:3`, finite rows, and stable atom count. The LJ parser validates type count, element order, positive epsilon/sigma/cutoff, complete pair rows, and the non-NEP minimum-image rule: every periodic cell thickness must exceed twice the largest cutoff.

## Audit technical output and statistics

```bash
python3 "$GPUMD_GUARD" audit-output \
  --plan gpumd-plan.json --input-audit gpumd-input-audit.json \
  --stdout gpumd.stdout --thermo thermo.out \
  --out gpumd-output-audit.json
```

Require one `version 5.3` banner, one start marker, one command-completion marker, one timing line, one terminal marker, no error/NaN marker, and exactly the planned number of 18-column thermo rows. Columns are interpreted using GPUMD's documented fixed order and units: temperature (K), kinetic and potential energy (eV), six pressure components (GPa), and nine cell-vector components (Å).

The guard discards only the predeclared equilibration prefix, computes a conservative autocorrelation effective-sample estimate and block-mean standard error, and applies only the project's declared bounds. It does not discover stationarity, manufacture independent replicas, or validate the potential's physical domain.

## Audit extxyz trajectory integrity

```bash
python3 "$GPUMD_GUARD" audit-trajectory \
  --plan gpumd-plan.json --input-audit gpumd-input-audit.json \
  --output-audit gpumd-output-audit.json --trajectory trajectory.xyz \
  --out gpumd-trajectory-audit.json
```

Require the planned frame count, atom count, species/site order, finite values, strictly increasing `Time` in fs, expected spacing, matching PBC, nonsingular cells, and declared per-atom properties. Wrapped `pos` and `unwrapped_position` remain distinct. The result is only a hash-bound handoff inventory; it does not instantiate missing shared run, structure, topology, segment, or trajectory records.

## Apply GPUMD-specific gates

- Pin release `v5.3` and commit `f2b46c5d528e985a5bf68becd442b18c0e04396c`. Never silently apply rolling v5.5 documentation to v5.3.
- Identify a native binary by source/build provenance, SHA-256, and the normal-run v5.3 banner. The reviewed source has no documented side-effect-free version flag; never run `gpumd --version` as a probe.
- Treat GPUMD, each potential/model file, and every dataset as independently licensed artifacts. Engine openness does not grant NEP model redistribution.
- Record whether the executable was built for NVIDIA CUDA or AMD ROCm/HIP, GPU model/capability, compiler/toolchain, precision-affecting build identity, and known-issues review before execution.
- Keep a separate NVE drift/time-step sensitivity study and model-domain validation when the scientific claim depends on them. No universal tolerance is embedded.
- Repeat non-propagating controls before every `run`. Appended `thermo.out` and extxyz files require a clean output destination or hash-bound segment accounting.
- Treat `dump_restart` as recoverability evidence, not proof of exact continuation. Record parent state hash and segment boundaries.
- Report effective sample size, uncertainty, replica coverage, finite-size/cutoff sensitivity, initial-state sensitivity, and model sensitivity where relevant.

## Preserve environment, legal, privacy, and execution boundaries

Read [references/environment-license-execution.md](references/environment-license-execution.md) and [references/execution-and-executable-map.md](references/execution-and-executable-map.md). Current official installation material requires a supported GPU stack; Apple Silicon is not a supported execution target. This fact does not prevent offline auditing.

Reports use safe labels and SHA-256 digests, not absolute paths. Keep hosts, usernames, scheduler IDs, private results, unpublished model contents, credentials, and restricted datasets outside source and reports. The exact v5.3 source headers and planned environment profiles record GPL-3.0-or-later; model and dataset terms remain independent.

The guard may create one new report file after refusing overwrite. Input paths are traversed component by component through stable directory descriptors; symlinked ancestors, FIFOs, and other non-regular inputs fail closed without blocking. Report publication retains and verifies the staging descriptor, then uses an atomic hard-link create-if-absent operation; it never uses replacement semantics, so a late target is preserved and the command fails. It may not execute software, access a network, install packages, alter calculation inputs, submit jobs, signal processes, or control resources.

## Interpret deterministic reports

- `0`: this local offline command passed;
- `2`: evidence failed, contradicted the plan, or violated safety;
- `3`: evidence or supported coverage is incomplete;
- `4`: internal tool error.

Always read JSON. `decision=pass` is command-local; `claim_ceiling=no_positive_claim`, `promotion_ready=false`, `promotion_authorized=false`, and `execution_authorized=false` remain invariant for this development Skill. Upstream reports are loaded from one identity-checked raw-byte snapshot and downstream lineage binds its exact SHA-256; the self-computed `report_fingerprint` is descriptive, never a trust root. `report_authenticity=unsigned-candidate-output` remains invariant, so only a separately controlled trusted manifest or signature can authenticate a report as evidence. `future_gate_ceiling` is descriptive only. Current maturity is at most `synthetic-validated`; legal version-matched real artifacts and an authorized independent integration run are still required for promotion. See [references/fail-closed-contract.md](references/fail-closed-contract.md), [references/role-handoff-model.md](references/role-handoff-model.md), [references/task-evidence-profiles.json](references/task-evidence-profiles.json), the canonical [`candidate-decision-table@1.0` weak-model routing table](references/weak-model-decision-table.json), [references/finding-catalog.json](references/finding-catalog.json), and [references/maturity-matrix.json](references/maturity-matrix.json).
