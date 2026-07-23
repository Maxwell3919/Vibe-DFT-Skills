---
name: lasp-rigorous-simulations
description: Create evidence-gap-aware LASP 3.7.3 plans for PES evaluation, SSW/global structure and reaction exploration, NN-potential active learning, and MD; route the verified Linux/Intel-MPI `Src/lasp` entry; and inventory opaque inputs, models, outputs, restart claims, and trajectories without inventing syntax, units, defaults, completion markers, license rights, or launching LASP.
---

# LASP Rigorous Simulations

This candidate is deliberately fail closed. Public author literature supports LASP 3.7 capabilities at a high level. The official LASP Hub page reviewed on 2026-07-22 identifies the CPU distribution as LASP 3.7.3 for Linux with Intel MPI/Compiler 2017+, executable `Src/lasp`, and direct/MPI launcher examples. The advertised manual/examples require authorized download and were not obtained, so complete input grammar, units/defaults, completion markers, restart specification, full compatibility, and software terms remain unimplemented. Never convert that narrower evidence gap into guessed syntax.

The candidate remains useful: it creates an explicit scientific plan, content-addresses opaque artifacts, checks privacy/legal declarations, flags corrupted generic text, validates project-authored extxyz structure independently of engine provenance, and produces a precise promotion delta. It never invokes LASP or claims a LASP run completed.

## Resolve the offline evidence guard

Resolve `LASP_SKILL_ROOT` to this candidate and use:

```bash
LASP_GUARD="$LASP_SKILL_ROOT/scripts/lasp_evidence_guard.py"
python3 "$LASP_GUARD" --help
```

Stop if the absolute path cannot be resolved. Do not copy the script into a calculation tree.

## Follow this low-reasoning workflow exactly

1. Inventory the bounded scientific objective, software/version claim, task, intended units, boundaries, ensemble, time step, model, seeds, restart ancestry, equilibration, production, observables, uncertainty rule, documents, environment, legal status, and execution authority.
2. Copy [examples/plan-request.json](examples/plan-request.json). Values are project declarations, not LASP defaults. Never invent a keyword, unit, tolerance, seed, restart field, output marker, dependency, or license.
3. Run `plan` only when every current schema field can be stated honestly. A
   pass means only that the generic gap-aware shape is internally complete;
   `claim_ceiling` remains `no_positive_claim` and `report_authenticity` remains
   `unsigned-candidate-output`. For global-structure/reaction search, the
   current schema is still MD-shaped and cannot encode search coverage,
   duplicate handling, recurrence, or termination. Never invent timestep,
   phases, or mean/block-mean observables merely to obtain a pass; use the
   documentary evidence matrix and report the missing machine profile.
4. Read [references/official-sources.json](references/official-sources.json) and [references/execution-and-executable-map.md](references/execution-and-executable-map.md). Use the 2024 author paper for capability context and the official download page for the 3.7.3 edition, Linux/Intel baseline, and `Src/lasp` launcher facts. Neither is a version-matched syntax/output/restart contract.
5. Run `audit-input` on opaque files, provenance, and the documentation attestation. It will return `incomplete` even when inventory checks pass because input semantics cannot be verified.
6. Stop before execution. The public page verifies `[LASP Installation DIR]/Src/lasp` and `mpirun -np 4 [LASP Installation DIR]/Src/lasp`, but not a side-effect-free version flag, arbitrary rank policy, input argument, working-file grammar, resource estimate, or execution authority. Do not invent any missing part.
7. Run `audit-output`. It can detect bounded text corruption/adverse markers and bind hashes, but it must return `incomplete` because no authoritative completion or observable grammar is implemented.
8. Run `audit-trajectory` on generic project-authored extxyz plus a hash-bound frame index. Format integrity can be measured; LASP provenance and technical completion remain unverified.
9. Report the exact evidence gaps and promotion delta. No automated command after `plan` can support a positive LASP claim.

## Route to the public task content

Read [references/public-capability-workflows.md](references/public-capability-workflows.md)
before planning PES evaluation, SSW/global structure search, surface/interface
search, reaction pathways, active learning/NN construction, MD, or performance.
It maps public author evidence to task-specific inputs, validation questions,
and stop conditions while deliberately omitting unverified LASP syntax.

Statements labeled **operational heuristic** are project-validation practices,
not LASP defaults. Keep `parser_supported=false`,
`operational_readiness=false`, and `no_positive_claim` until the authorized
3.7.3 manual, examples, terms, parsers, fixtures, and integration evidence close
the corresponding gaps.

The current `plan` vocabulary is limited to `nve`, `nvt`, `npt`,
`global-structure-search`, and `reaction-search`. For PES-only evaluation,
active learning, NN training, ASOP, or ML-interface, use the reference to create
a documentary evidence matrix and report the missing machine-readable profile;
never force the work into a misleading supported task label.

## Create a gap-aware scientific plan

```bash
python3 "$LASP_GUARD" plan --request plan-request.json --out lasp-plan.json
```

The plan requires anonymous IDs, exact `lasp_version=3.7.3` under the LASP 3.7 literature capability context, a literature-described task, objective, bounded claim target, explicitly project-declared units, three boundary booleans, ensemble, positive time step with unit, model identity/source/license status, new or opaque-state lineage, seed policy, equilibration and production phases, named observables, estimator and uncertainty bounds, explicit unavailable-document flags, and `execute_external_software=false`.

The supported plan vocabulary includes standard NVE/NVT/NPT MD and design-only global-structure/reaction search because those capability classes are described in the author paper. The schema remains MD-shaped: it does not represent a search algorithm, composition/cell move space, duplicate rule, unique-minimum discovery curve, recurrence, coverage, or termination. Therefore a search-shaped `plan=pass` is only generic inventory completeness, not SSW-plan completeness. This does not assert exact keywords, algorithms, defaults, thermostats, barostats, search parameters, or file formats.

## Inventory opaque inputs

```bash
python3 "$LASP_GUARD" audit-input \
  --plan lasp-plan.json --input opaque-input.txt --model opaque-model.extxyz \
  --provenance model-provenance.json \
  --documentation-attestation documentation-attestation.json \
  --out lasp-input-inventory.json
```

The guard verifies bounded regular files, ASCII/no-NUL text, safe labels, SHA-256, exact provenance closure, source/license declarations for the fixture, documentation-attestation consistency, and common credential/private-path leakage markers. It does not parse or validate LASP syntax. The example input says explicitly that it is not LASP syntax.

Expected unresolved gates are:

- version-matched manual and authoritative input grammar;
- defaults and units mapping;
- model/potential file grammar and compatibility;
- ensemble, timestep, seed and boundary keyword mapping;
- restart/state retention and exactness semantics;
- environment/build/executable identity;
- software license and redistribution terms.

The executable basename, Linux platform, Intel MPI/Compiler 2017+ baseline, and two public launcher examples are no longer evidence gaps. Exact binary/edition compatibility, ABI/runtime closure, side-effect-free version probing, input/output/restart grammar, resources, and complete terms remain gaps.

## Inventory opaque output

```bash
python3 "$LASP_GUARD" audit-output \
  --plan lasp-plan.json --input-audit lasp-input-inventory.json \
  --output synthetic-output.txt --attestation output-attestation.json \
  --out lasp-output-inventory.json
```

The tool requires an explicit artifact-origin attestation, scans for non-finite/fatal/error markers, counts lines/bytes, and binds the exact file. It never interprets a phrase as LASP completion, extracts observables, or claims convergence. Project-authored synthetic text is legal parser evidence only.

## Check generic extxyz format without claiming LASP provenance

```bash
python3 "$LASP_GUARD" audit-trajectory \
  --plan lasp-plan.json --input-audit lasp-input-inventory.json \
  --output-audit lasp-output-inventory.json \
  --trajectory trajectory.extxyz --frame-index frame-index.json \
  --out lasp-trajectory-inventory.json
```

Check atom/frame counts, required `pbc`, `Lattice`, `Properties=species:S:1:pos:R:3`, finite values, stable species order, nonsingular cells, frame-index hash, monotonic step/time, and declared time units. This is a project-defined extxyz integrity result, not evidence that LASP wrote the file. Without a stable site ID, same-species atom permutations cannot be detected.

## Keep all scientific gates explicit

- Topology/model identity and license must be independent of LASP software identity.
- Units, boundaries, ensemble, timestep, thermostat/barostat/search controls, seed behavior, output cadence, restart state, and observables remain project intentions until mapped to an authoritative manual.
- Equilibration and production must be separated before execution. Do not choose discard ranges after seeing a desired result.
- Predeclare convergence, drift, finite-size, model-domain, replica, effective-sample, and uncertainty acceptance rules appropriate to the eventual method.
- Completion, numerical stability, statistical sufficiency, physical validity, and scientific acceptance remain distinct.
- A capability statement in a research paper is not proof that a particular binary/version/input executed that capability correctly.

## Preserve environment, license, privacy, and execution boundaries

Read [references/environment-license-execution.md](references/environment-license-execution.md) and [references/execution-and-executable-map.md](references/execution-and-executable-map.md). State only the public 3.7.3 Linux/Intel MPI/Compiler 2017+ baseline and `Src/lasp` commands. Do not infer architecture, ABI, exact compiler/MPI release, GPU, Python/library, license mechanism, CLI flags, input filenames, or resource requirements. Treat LASP software terms as restricted pending direct verification; the public edition/expiry summary is not a complete license.

Keep hostnames, usernames, scheduler IDs, private paths, credentials, unpublished structures/results, and restricted model bodies out of source and reports. Reports expose safe labels, hashes, sizes, and bounded metadata only.

The tool may create one new report after refusing overwrite. Input paths are traversed component by component through stable directory descriptors; symlinked ancestors, FIFOs, and other non-regular inputs fail closed without blocking. Report publication retains and verifies the staging descriptor, then uses an atomic hard-link create-if-absent operation; it never uses replacement semantics, so a late target is preserved and the command fails. It may not execute, install, access a network, change calculation files, submit jobs, signal processes, or manage resources.

## Interpret deterministic reports

- `0`: the gap-aware `plan` passed its local completeness checks;
- `2`: unsafe, invalid, contradictory, corrupt, or privacy/legal evidence;
- `3`: expected documentary or semantic incompleteness;
- `4`: internal error.

Always read JSON. `claim_ceiling` and `future_gate_ceiling` remain `no_positive_claim`; `promotion_ready`, `promotion_authorized`, and `execution_authorized` remain false. Upstream reports are loaded from one identity-checked raw-byte snapshot and downstream lineage binds its exact SHA-256; the self-computed `report_fingerprint` is descriptive, never a trust root. `report_authenticity=unsigned-candidate-output` remains invariant, so only a separately controlled trusted manifest or signature can authenticate a report as evidence. `audit-input`, `audit-output`, and `audit-trajectory` remain `incomplete` even when their format metrics pass. Current maturity is `documentary-inventory-only`. Activation requires an authorized version-matched manual and terms, independent parser design, legal real artifacts, adversarial tests, authorized integration, shared-interface alignment, registry promotion, and installed-copy verification. See [references/fail-closed-contract.md](references/fail-closed-contract.md), [references/role-handoff-model.md](references/role-handoff-model.md), [references/evidence-gap-register.json](references/evidence-gap-register.json), [references/task-evidence-profiles.json](references/task-evidence-profiles.json), the canonical [`candidate-decision-table@1.0` weak-model routing table](references/weak-model-decision-table.json), [references/finding-catalog.json](references/finding-catalog.json), and [references/maturity-matrix.json](references/maturity-matrix.json).
