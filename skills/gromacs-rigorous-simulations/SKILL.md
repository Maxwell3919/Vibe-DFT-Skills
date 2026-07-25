---
name: gromacs-rigorous-simulations
description: Design, resolve exact official commands for, safely probe, execute when explicitly authorized, troubleshoot, and fail-closed audit GROMACS 2026.3 molecular-dynamics workflows. Use for installation/build identity, gmx command discovery, pdb2gmx/solvation/ionization, grompp/mdrun, .mdp/.top/.itp/.gro/.tpr/.cpt/.edr/trajectory formats, NVE/NVT/NPT/minimization, checkpoint continuation, native analysis tools, force-field provenance, completion/log failures, sampling uncertainty, and deciding what a GROMACS artifact can support.
---

# GROMACS Rigorous Simulations

Read [the local official-manual cache route](references/manual-cache-route.md) before using any external GROMACS documentation body.

Keep system preparation, preprocessor success, execution completion, ensemble sampling, numerical stability, model validity, and human scientific acceptance separate. This development Skill now contains concrete version-bound commands and workflows. Its manual resolver may run only fixed version/help probes; its evidence guard never invokes `grompp`, `mdrun`, a scheduler, or a remote host. Run scientific or state-changing provider commands only when the user explicitly authorizes their exact scope.

## Start manual-first

Resolve this directory as `GROMACS_SKILL_ROOT`, then validate and search the bundled 2026.3 sources before composing a command:

```bash
GROMACS_MANUAL="$GROMACS_SKILL_ROOT/scripts/gromacs_manual.py"
python3 -B "$GROMACS_MANUAL" validate
python3 -B "$GROMACS_MANUAL" commands --query grompp
python3 -B "$GROMACS_MANUAL" recipes --category restart
python3 -B "$GROMACS_MANUAL" show-recipe continue-from-checkpoint
```

Use [official-command-catalog.json](references/official-command-catalog.json) for command discovery, [task-recipes.json](references/task-recipes.json) for exact argv/stdin/input/output/restart/failure/scientific recipes, [core-file-formats.json](references/core-file-formats.json) for native file semantics, and [operational-workflows.md](references/operational-workflows.md) for the content-level preparation, MDP, restart, failure, trajectory, and performance audit. The states are deliberately separate:

- `official-index-listed`: the pinned command index lists it;
- `official-manual-recipe`: exact syntax has a pinned official recipe;
- `native-not-run`: no local provider command ran;
- `native-validated`: only the exact safe probe or captured provider run named by evidence ran.

If an operation is only listed, or a recipe still contains an unresolved `<parameter>`, stop. Do not invent syntax, selections, force-field choices, seeds, tolerances, or acceptance thresholds.

## Probe the actual executable

```bash
python3 -B "$GROMACS_MANUAL" probe-native --executable gmx
```

The probe runs only `gmx --version` and `gmx help commands` in a fresh temporary directory, returns hashes and parsed safe fields, and requires exact version `2026.3` plus `grompp`, `mdrun`, `check`, and `energy`. It does not run a simulation. Alternate names such as `gmx_mpi`, `gmx_d`, and `gmx_mpi_d` must be selected explicitly. The current host probe is [native-not-run](references/native-capability.json): none of those names or the `gromacs`/`gmxapi` Python distributions was installed on 2026-07-19. Do not install or download to turn that absence into a pass.

## Execute an official recipe only with authority

For a requested real run, apply this sequence:

1. Prove the exact executable/version/build and hash it.
2. Select one recipe; resolve every parameter and interactive selection from project evidence.
3. Run the offline `plan` and `audit-input` gates. For preprocessing, retain the complete topology closure, `grompp` argv, stdout/stderr, exit code, `mdout.mdp`, processed topology and TPR hash. Never use `-maxwarn` as readiness evidence.
4. Show the exact argv/stdin/output paths and obtain explicit authorization for provider execution, compute, writes, scheduler/remote work, and costs in scope.
5. Execute in a fresh or lineage-bound directory. Capture exit code and immutable stdout/stderr/log hashes. A nonzero exit blocks; zero alone is insufficient.
6. Verify the expected files are new/nonempty and run the relevant native integrity recipe (`gmx check`, `gmx dump`, or `gmx report-methods`) before the offline output/trajectory gates.
7. Apply observable-specific convergence, sampling, uncertainty, model-domain, finite-size, cutoff/PME, time-step, ensemble and replica gates. Provider completion is never scientific acceptance.

The typical accepted route is explicit preparation → minimization → NVT equilibration → NPT equilibration when physically appropriate → immutable production → native integrity checks → declared analysis. Each arrow is a separate artifact/lineage boundary. Do not reuse desired test/OOD outcomes to tune the protocol.

Before drafting or auditing any conventional workflow, read the relevant section of [operational-workflows.md](references/operational-workflows.md). It labels exact-version official behavior, operational heuristics, project decisions, and observed evidence separately; none of its command families attest native execution.

## Resolve the candidate tool

Resolve `GROMACS_SKILL_ROOT` to this directory, then use an absolute script path:

```bash
GROMACS_GUARD="$GROMACS_SKILL_ROOT/scripts/gromacs_guard.py"
python3 "$GROMACS_GUARD" --help
```

Stop if this path cannot be resolved. Do not copy the guard into a calculation directory.

## Follow the low-reasoning workflow exactly

1. Inventory the requested claim, GROMACS executable version, task, system identity, force-field/topology closure, units, PBC, ensemble, integrator, time step, seed policy, restart ancestry, equilibration phase, production phase, observables, estimator, uncertainty method, and stop criteria.
2. Create a JSON request from [examples/plan-request.json](examples/plan-request.json). Never invent a tolerance, seed, model source, license, or parent checkpoint.
3. Run `plan`. Continue only when the report decision is `pass`; the plan still has `no_positive_claim`.
4. Read [references/official-sources.json](references/official-sources.json). Match the executable banner to a version-specific official source before stating syntax or defaults. A `current` URL is only a discovery route, not proof for an older executable. Use the manual resolver; a command listing is not a runnable recipe.
5. Run `audit-input` on the `.mdp`, coordinate file, root topology, and provenance manifest. Resolve every quoted include inside the declared root. Angle-bracket or environment-dependent includes remain incomplete.
6. If a real run is requested, complete every preceding gate, resolve one exact recipe, show argv/stdin/outputs, and obtain explicit authorization. The manual resolver never launches the run; an authorized execution layer or direct user-approved command must capture it.
7. Run `audit-output` only on an unchanged passing plan and matching log/series evidence. Completion does not establish equilibration, statistical sufficiency, or physical validity.
8. Run `audit-trajectory` on a text `.gro` trajectory or a predeclared sidecar inventory. Binary XTC/TRR/TNG/H5MD contents are unsupported offline until a version-pinned official adapter produces hash-bound evidence.
9. Report every failed, incomplete, unsupported, or not-assessed gate. Because this lifecycle is `development`, every current report remains `claim_ceiling=no_positive_claim`; `future_gate_ceiling` only names post-promotion potential. Expert review and scientific acceptance remain external.

Treat every guard report as `report_authenticity=unsigned-candidate-output`. The guard validates the complete upstream report shape and self fingerprint, then binds downstream lineage to the SHA-256 of the exact verified raw report bytes. The self fingerprint is an integrity checksum, not a trust root. Only a separately verified trusted manifest or signature outside this candidate may attest report origin; without one, no report is execution, promotion, or scientific evidence.

## Create the plan

```bash
python3 "$GROMACS_GUARD" plan \
  --request plan-request.json \
  --out gromacs-plan.json
```

The request must explicitly define:

- `gromacs_version`, `task`, anonymous `case_id` and `protocol_id`;
- objective and bounded claim target;
- fixed GROMACS units: `nm`, `ps`, `kJ/mol`, `bar`, `K`;
- three-axis PBC, integrator, ensemble and positive `timestep_ps`;
- topology and force-field identities with independent source and license declarations;
- `new` or `checkpoint-continuation` lineage;
- seed policy, equilibration/production step counts, and phase acceptance checks;
- named observables with units, estimator, uncertainty method, minimum effective sample size, and an accepted uncertainty threshold.

Do not treat the plan's threshold as a recommendation from this Skill. It is user/project acceptance input.

## Audit GROMACS inputs

```bash
python3 "$GROMACS_GUARD" audit-input \
  --plan gromacs-plan.json --mdp production.mdp \
  --coordinates start.gro --topology topol.top \
  --provenance model-provenance.json \
  --out gromacs-input-audit.json
```

The supported core checks explicit `integrator`, `dt`, `nsteps`, `pbc`, thermostat/barostat coupling, velocity generation, continuation mode, output cadence, topology include closure, coordinate grammar, atom counts, file hashes, model sources, and license status. It rejects duplicate `.mdp` assignments even though GROMACS can apply the last value; this is an audit policy to remove ambiguity. It rejects `-maxwarn` as an evidence route and never treats `mdout.mdp` or a TPR as audited unless a future official adapter binds them.

For a new stochastic start require explicit `gen-vel=yes` and a nonnegative `gen-seed`. For checkpoint continuation require `continuation=yes`, `gen-vel=no`, a parent record ID, and a checkpoint SHA-256. Checkpoint identity is necessary but does not prove bitwise reproducibility across hardware, build, MPI layout, GPU reductions, or dynamic load balancing.

## Audit output and sampling evidence

```bash
python3 "$GROMACS_GUARD" audit-output \
  --plan gromacs-plan.json --input-audit gromacs-input-audit.json \
  --log md.log --series thermo.csv \
  --out gromacs-output-audit.json
```

Require exactly one matching `mdrun` version banner, one terminal marker, the planned final step, no fatal/constraint/NaN marker, and input-audit hash binding. The CSV must use `step` plus columns named by the plan observables. The guard discards only the predeclared equilibration range, estimates autocorrelation and effective sample size conservatively, calculates block-mean uncertainty, and checks the user-declared bound. It does not discover equilibration, prove stationarity, or replace replica analysis.

Any warning suppression, LINCS/SETTLE warning, energy blow-up, truncated log, concatenated run, missing series, low effective sample size, or excessive uncertainty blocks its local positive claim.

## Audit trajectory integrity

```bash
python3 "$GROMACS_GUARD" audit-trajectory \
  --plan gromacs-plan.json --input-audit gromacs-input-audit.json \
  --output-audit gromacs-output-audit.json \
  --trajectory trajectory.gro --out gromacs-trajectory-audit.json
```

Check frame count, atom count, stable site order, finite coordinates and boxes, monotonically increasing `t=` values, expected time spacing, PBC/cell consistency, source hashes, and segment/restart lineage. Never infer unwrapped coordinates from wrapped `.gro` positions. Do not claim velocities or forces exist unless the format and parser observed them.

Use the canonical `atomistic-trajectory-manifest@1.0` only after required upstream structure, topology, run, frame-index, and segment records exist. This candidate reports a handoff inventory; it must not fabricate missing record references.

## Apply GROMACS-specific scientific gates

- Treat topology plus every included parameter file as one content-addressed closure. Record force-field family, release, water/ion model, custom parameters, combination rules, source URL, license, and hashes.
- Treat `gmx grompp` preprocessing as a future authorized adapter. A zero exit code with warnings overridden is not input readiness.
- Use GROMACS native units exactly. Convert external structures and parameters before audit and record the conversion lineage.
- Distinguish `tcoupl`/`pcoupl` setup from ensemble validity. Berendsen pressure coupling cannot support a production NPT ensemble claim.
- Check time-step sensitivity and NVE drift against a predeclared observable and tolerance; no universal drift threshold is embedded.
- Separate equilibration diagnostics from production samples. Do not discard samples after looking at the desired result without recording a new protocol.
- Report autocorrelation, effective sample size, block sensitivity, uncertainty and replica coverage. A long trajectory is not automatically statistically sufficient.
- Test finite-size, cutoff, PME/electrostatic, constraint, thermostat/barostat, model and initial-state sensitivity when the scientific claim depends on them.

## Preserve safety, privacy, environment, and license boundaries

Read [references/environment-license-execution.md](references/environment-license-execution.md) before any environment or execution discussion. Keep hosts, usernames, scheduler IDs, tokens, private paths, unpublished results, checkpoint bodies, and restricted force-field contents out of source and reports. Reports contain safe labels and SHA-256 only.

GROMACS is open-source, but bundled libraries, force fields, topologies, custom parameters, and user data have independent terms. Never infer model redistribution rights from the GROMACS license.

The offline evidence guard may write a new report path after refusing overwrite, but it never executes a provider binary, accesses the network, submits a job, signals a process, alters a calculation tree, or installs software. The manual resolver is separately limited to the fixed safe native probe documented above. A scientific provider run belongs to a distinct execution layer and requires the exact recipe, inputs, executable, resources, output tree, and authorization to be recorded before launch.

All reads use a retained descriptor for a component-by-component `openat` traversal with `O_DIRECTORY|O_NOFOLLOW`; the final file is opened with `O_NONBLOCK|O_NOFOLLOW` and must be a single-link regular file, so a FIFO cannot block the guard. Request and evidence bases remain bound to the same retained directory identity. Report publication retains the staging file descriptor, verifies inode, size, and payload before and after publication, and uses a same-directory hard link as atomic create-if-absent. It never uses replace semantics. On a post-link failure it removes only the target proven to be the inode created by that call; an independently created or substituted target is never rolled back. If the platform cannot provide these descriptor-relative primitives, the operation is incomplete.

## Interpret reports

Use stable exits:

- `0`: the requested local offline gate passed;
- `2`: evidence is invalid, contradictory, unsafe, or failed;
- `3`: evidence is incomplete or the feature/format/version is unsupported;
- `4`: internal tool error.

Read JSON after every exit. `decision=pass` applies only to that offline gate. Current `claim_ceiling` is always `no_positive_claim`, and `promotion_ready`, `promotion_authorized`, and `execution_authorized` are always false. `future_gate_ceiling` is descriptive promotion potential only. Current maturity remains at most `synthetic-validated` until legal version-matched real artifacts and official adapters are independently validated.

Read [references/fail-closed-contract.md](references/fail-closed-contract.md), [references/role-handoff-model.md](references/role-handoff-model.md), [references/task-evidence-profiles.json](references/task-evidence-profiles.json), the canonical [`candidate-decision-table@1.0` weak-model routing table](references/weak-model-decision-table.json), [references/finding-catalog.json](references/finding-catalog.json), and [references/maturity-matrix.json](references/maturity-matrix.json) when extending or interpreting coverage. Evaluate decision cases by ascending priority and use the final evidence-free default when no earlier condition is established.
