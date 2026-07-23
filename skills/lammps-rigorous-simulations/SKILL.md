---
name: lammps-rigorous-simulations
description: Design, resolve exact official commands for, safely probe, execute when explicitly authorized, troubleshoot, and fail-closed audit LAMMPS 4Jul2026 atomistic workflows. Use for source/build identity, -help/style probes, input scripts/includes, data files, units/boundaries, force-field and ML-potential provenance, minimization/NVE/NVT/NPT, binary restart lineage, logs/dumps, RDF/MSD/VACF/rerun/Colvars recipes, sampling uncertainty, environment/license evidence, and deciding what a LAMMPS artifact can support.
---

# LAMMPS Rigorous Simulations

Treat a LAMMPS input as executable code. Separate script safety, parser coverage, build capability, topology, model provenance, numerical protocol, restart lineage, technical completion, trajectory integrity, statistics, and scientific acceptance. This development Skill contains concrete 4Jul2026 commands and workflows. Its manual resolver may run only the fixed `-help` probe; the evidence guard never invokes LAMMPS, Python embedded in LAMMPS, a shell, a plugin, scheduler, or network. Run provider simulations only with explicit user authorization for the exact reviewed scope.

## Start manual-first

```bash
LAMMPS_MANUAL="$LAMMPS_SKILL_ROOT/scripts/lammps_manual.py"
python3 -B "$LAMMPS_MANUAL" validate
python3 -B "$LAMMPS_MANUAL" commands --query restart
python3 -B "$LAMMPS_MANUAL" recipes --category molecular-dynamics
python3 -B "$LAMMPS_MANUAL" show-recipe official-lj-melt-smoke --executable lmp --require-ready
```

Use [official-command-catalog.json](references/official-command-catalog.json) for the pinned general-command and style-family indexes, [task-recipes.json](references/task-recipes.json) for exact argv/input-script/input/output/restart/failure/scientific recipes, [core-file-formats.json](references/core-file-formats.json) for script/data/restart/dump/log/model semantics, and [operational-workflows.md](references/operational-workflows.md) for content-level script, model, neighbor, fix, restart, replica, accelerator, failure, and trajectory review. Keep `official-index-listed`, `official-manual-recipe`, `native-not-run`, and `native-validated` separate. A style listed in the manual is not necessarily compiled into the selected binary.

If a recipe retains an unresolved `<parameter>`, `--require-ready` fails closed. Resolve it from project evidence; do not invent unit conversions, pair coefficients, atom-type maps, seeds, damping times, timesteps, run lengths, or acceptance thresholds.

## Probe the exact binary and styles

```bash
python3 -B "$LAMMPS_MANUAL" probe-native \
  --executable lmp --require-style lj/cut --require-style nve
```

This runs only `<executable> -help` in a fresh temporary directory, requires `LAMMPS (4 Jul 2026)`, hashes the executable/help streams, and checks requested style strings. It never runs an input script. The current host record is [native-not-run](references/native-capability.json): no common LAMMPS executable or Python distribution was installed on 2026-07-19. Do not download or install to manufacture native evidence.

## Execute a reviewed recipe only with authority

1. Prove the exact banner, executable SHA-256, build configuration, packages and every required style.
2. Select one recipe and resolve every placeholder. Audit the script as code, complete literal include/data/model closure, units, types, boundaries, seeds, integrator ownership and restart ancestry.
3. Show exact argv, input bytes/closure, work directory, outputs and resource scope; obtain explicit authorization for all provider, compute, scheduler, remote and filesystem effects.
4. Run in a fresh or lineage-bound directory and capture exit code plus screen/log hashes. Any nonzero exit blocks. Zero alone is insufficient.
5. Require the exact banner, intended thermo table, planned final step and `Loop time`; block `ERROR`, adverse `WARNING`, lost atoms, non-finite values, segmentation, missing/truncated output, or unexpected file changes.
6. Verify data/restart/dump artifacts, then apply time-step, drift, cutoff/finite-size, model-domain, ensemble, replica, stationarity, autocorrelation/ESS and uncertainty gates.

The normal route is exact build/style probe → preparation/minimization → NVT/NPT equilibration when justified → immutable NVE/ensemble production → restart/segment verification → declared rerun/RDF/MSD/VACF analysis. Each segment and transform gets a new lineage record.

Before drafting or auditing a real input, read the relevant section of [operational-workflows.md](references/operational-workflows.md). It keeps official release behavior, operational heuristics, project decisions, and observed evidence separate; none of its command families attest native execution.

## Resolve the offline guard

Resolve `LAMMPS_SKILL_ROOT` to this candidate and call the script in place:

```bash
LAMMPS_GUARD="$LAMMPS_SKILL_ROOT/scripts/lammps_guard.py"
python3 "$LAMMPS_GUARD" --help
```

Stop if the absolute path cannot be resolved. Do not copy the guard into a calculation tree.

## Follow the low-reasoning workflow exactly

1. Inventory the claim, exact LAMMPS release date, executable/build hash, packages and styles, task, topology, atom style, `units`, unit map, `boundary`, pair model, ensemble, time step, every seed, restart ancestry, equilibration, production, observables, uncertainty rule, output cadence, environment, legal status, and execution authority.
2. Copy [examples/plan-request.json](examples/plan-request.json). Replace values only when evidence exists; never infer units, pair coefficients, seed, model license, restart portability, or tolerance.
3. Run `plan`. Continue only for `decision=pass`; planning never supports a positive scientific claim.
4. Match release `4Jul2026` to [references/official-sources.json](references/official-sources.json), validate the command/recipe catalogs, then bind [examples/build-manifest.json](examples/build-manifest.json) to the exact executable and required styles. A version banner alone does not prove an optional package/style exists.
5. Run `audit-input`. The guard recursively resolves literal relative `include` files inside the root and rejects dynamic control flow, variable expansion, path escape, and executable extension surfaces.
6. Stop before execution until an execution layer or direct user approval independently authorizes the exact input closure, executable, host, resources, output tree, and time window. The manual resolver never launches a simulation.
7. Run `audit-output` on a matching passing plan/input report and exact log segment. A `Loop time` line is technical evidence, not equilibrium or physical validity.
8. Run `audit-trajectory` on the planned text custom dump. Verify timestep/frame/site/cell/boundary continuity and coordinate semantics.
9. Report every failed, incomplete, unsupported, and not-assessed gate. Because the lifecycle is `development`, every current report remains `claim_ceiling=no_positive_claim`; `future_gate_ceiling` is post-promotion potential only. Expert acceptance is external.

Treat every guard report as `report_authenticity=unsigned-candidate-output`. The guard validates the complete upstream report shape and self fingerprint, then binds downstream lineage to the SHA-256 of the exact verified raw report bytes. The self fingerprint is an integrity checksum, not a trust root. Only a separately verified trusted manifest or signature outside this candidate may attest report origin; without one, no report is execution, promotion, or scientific evidence.

## Create the plan

```bash
python3 "$LAMMPS_GUARD" plan --request plan-request.json --out lammps-plan.json
```

The supported fixture profile is `units lj`, `atom_style atomic`, orthogonal `boundary p p p`, analytic `pair_style lj/cut`, one `fix ... nve`, a new velocity-seeded start, and one deterministic run segment. This narrow slice exists to make pass/fail claims defensible. `real`, `metal`, `si`, `cgs`, `electron`, `micro`, and `nano` units; molecular/reactive topologies; long-range electrostatics; constraints; rigid bodies; granular models; hybrid pair styles; ML potentials; NVT/NPT; deformation; replica methods; and package-dependent commands stay design-only until separately sourced and tested.

The plan must include an explicit unit-style-specific semantic map. Reduced LJ values are not SI quantities and must never be relabeled as kelvin, eV, ps, or GPa without an external parameterized conversion record.

## Audit inputs and script safety

```bash
python3 "$LAMMPS_GUARD" audit-input \
  --plan lammps-plan.json --input in.lammps --data system.data \
  --build-manifest build-manifest.json --provenance model-provenance.json \
  --out lammps-input-audit.json
```

The parser supports a fixed allowlist and literal relative includes. It refuses `$` expansion and `variable`, `if`, `jump`, `next`, `label`, `shell`, `python`, `geturl`, `plugin`, `quit`, and dynamic `run every`. Unknown commands are incomplete, never silently accepted. Include targets must be regular non-symlink files within the root; cycles and duplicate ambiguity block.

The supported input audit checks ordering and uniqueness of `units`, `atom_style`, `boundary`, and `read_data`; exact data atom/type counts, IDs, box and `Atoms # atomic` rows; `pair_style lj/cut` cutoff and numeric `pair_coeff`; minimum-image cell length; build style availability; one integrating `fix nve`; no double integration; explicit `velocity ... create ... seed`; time step; `thermo_style`; `thermo_modify lost error`; custom dump identity and image flags; restart cadence; run steps; provenance hashes and licenses.

For `binary-continuation`, require parent run ID, restart SHA-256, prior version/build identity, and `exact_continuation_claim=false`. LAMMPS binary restarts are not a portable archival format and do not preserve every command-defined object. Same executable/platform is an expectation, not a proof of bitwise identity; some stochastic/fix and neighbor-order effects can yield only statistical continuation. The current parser binds such evidence but returns incomplete until a version/build-specific binary adapter exists.

## Audit log and sampling

```bash
python3 "$LAMMPS_GUARD" audit-output \
  --plan lammps-plan.json --input-audit lammps-input-audit.json \
  --log log.lammps --out lammps-output-audit.json
```

Require one exact `LAMMPS (4 Jul 2026)` banner, one expected thermo table, all planned steps, one matching `Loop time ... for 12 steps with 2 atoms`, and no `ERROR`, `WARNING`, lost-atom, non-finite, segmentation, or unsafe-command marker. The candidate intentionally blocks all warnings in its narrow core; later profiles may introduce version-matched warning classification.

Discard only the predeclared equilibration prefix. Compute a conservative autocorrelation effective-sample count and block-mean standard error, then apply the project's declared thresholds. Do not tune discard or bounds after inspecting the desired outcome. A long log does not prove stationarity or independent sampling.

## Audit custom trajectory

```bash
python3 "$LAMMPS_GUARD" audit-trajectory \
  --plan lammps-plan.json --input-audit lammps-input-audit.json \
  --output-audit lammps-output-audit.json --trajectory trajectory.lammpstrj \
  --out lammps-trajectory-audit.json
```

The supported orthogonal custom dump requires `ITEM: TIMESTEP`, atom count, `BOX BOUNDS pp pp pp`, and `ATOMS id type x y z ix iy iz`. Check expected frames/timesteps, constant atom IDs/types, unique sites, finite wrapped positions, integer image flags, box consistency, and source hashes. For orthogonal cells, wrapped coordinates plus image flags permit a declared unwrapping reconstruction; triclinic/scaled/general-triclinic variants remain unsupported until their own parser is tested.

The audit emits only a handoff inventory. It does not fabricate canonical structure, topology, run, frame-index, segment, or trajectory manifests.

## Apply LAMMPS-specific scientific gates

- A LAMMPS version is a release date. Record the exact banner, executable SHA-256, source revision if known, packages, styles, accelerator suffix, compiler, MPI, FFT, and GPU/Kokkos configuration.
- `units` changes input, data, coefficients, defaults, and output meanings. Verify potential-file `UNITS` metadata when relevant; absence transfers responsibility to the user and cannot be guessed.
- Distinguish integration fixes from thermostat-only fixes. Do not integrate one atom group twice, and do not assume every thermostat advances positions.
- Treat `thermo_modify lost error` as required for this core. Lost atoms, NaNs, unstable neighbor behavior, and warning suppression block acceptance.
- Record pair coefficients, mixing, cutoff, shift/tail choices, special-bonds/exclusions, neighbor settings, and model files as one provenance closure where applicable.
- Validate time-step sensitivity, NVE drift, finite-size/cutoff behavior, initial-state/seed sensitivity, replica coverage, model domain, effective samples, and uncertainty according to the scientific claim. No universal threshold is embedded.
- Never claim restart exactness solely because the run continued. Bind every segment and record portability and reproducibility limitations.

## Preserve environment, legal, privacy, and authorization boundaries

Read [references/environment-license-execution.md](references/environment-license-execution.md). LAMMPS is GPL-2.0 software, but potential files, plugins, ML models, packages, datasets, and outputs may have separate terms. Engine licensing never grants model redistribution.

Reports contain safe IDs, basenames, hashes, and bounded metrics—not absolute paths, hosts, usernames, scheduler IDs, tokens, private model contents, or unpublished results. The offline evidence guard may create one new report after refusing overwrite, but it never executes a provider binary, installs software, accesses a network, alters input trees, submits jobs, signals processes, or controls resources. The manual resolver is separately limited to the fixed `-help` probe documented above. A scientific provider run belongs to a distinct execution layer and requires the exact recipe, script closure, executable, resources, output tree, and authorization to be recorded before launch.

All reads use a retained descriptor for component-by-component `openat` traversal with `O_DIRECTORY|O_NOFOLLOW`; the final file is opened with `O_NONBLOCK|O_NOFOLLOW` and must be a single-link regular file, so a FIFO cannot block the guard. Request and evidence bases remain bound to the same retained directory identity. Report publication retains the staging file descriptor, verifies inode, size, and payload before and after publication, and uses a same-directory hard link as atomic create-if-absent. It never uses replace semantics. On a post-link failure it removes only the target proven to be the inode created by that call; an independently created or substituted target is never rolled back. If the platform cannot provide these descriptor-relative primitives, the operation is incomplete.

## Interpret reports

- `0`: local offline gate passed;
- `2`: invalid, contradictory, unsafe, or failed evidence;
- `3`: incomplete or unsupported evidence/version/feature;
- `4`: internal error.

Always inspect JSON. Current `claim_ceiling=no_positive_claim`; `promotion_ready`, `promotion_authorized`, and `execution_authorized` remain false even for a passing offline gate. `future_gate_ceiling` is descriptive only. Current maturity is at most `synthetic-validated`. Activation still requires legal real artifacts, an independent authorized integration run, shared-interface alignment, adversarial acceptance, registry promotion, and installed-copy verification. Read [references/fail-closed-contract.md](references/fail-closed-contract.md), [references/role-handoff-model.md](references/role-handoff-model.md), [references/task-evidence-profiles.json](references/task-evidence-profiles.json), the canonical [`candidate-decision-table@1.0` weak-model routing table](references/weak-model-decision-table.json), [references/finding-catalog.json](references/finding-catalog.json), and [references/maturity-matrix.json](references/maturity-matrix.json). Evaluate cases by ascending priority and use the final evidence-free default when no earlier condition is established.
