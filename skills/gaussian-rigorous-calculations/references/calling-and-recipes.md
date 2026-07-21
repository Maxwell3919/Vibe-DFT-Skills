# Gaussian calling and recipe boundary

This guide answers two different questions without conflating them:

1. What does the public first-party Gaussian documentation say the real entry point
   and workflow are?
2. What may this development Skill actually do on the current machine?

The answer to the second question is still **offline planning/audit only**. No
Gaussian executable was found, the software is proprietary, current-host support is
not established, and execution was not authorized. The machine-readable
[`feature-catalog.json`](feature-catalog.json) and
[`task-recipes.json`](task-recipes.json) therefore mark every provider operation
`native-not-run` and every recipe `execution_authorized=false`.

## Select a path

| Request | First action | Guard status | Provider handoff |
|---|---|---|---|
| Inspect a narrow synthetic SP/Opt/Freq/Opt+Freq input or log | Use `gaussian_guard.py` and the task evidence profile | Implemented offline | None |
| Learn exact input section order or route syntax | Resolve `g16-input`, `g16-route`, and `g16-link0` in the feature catalog | Documentation only | None |
| Plan a real licensed SP/Opt/Freq job | Select one recipe, freeze all preconditions and identities, and use `calculation-workflows.md` | Synthetic guard only where explicitly stated; guard cannot authorize | Trusted licensed platform only |
| Diagnose SCF/geometry/frequency failure | Preserve failed bytes, use `troubleshooting-and-audit.md`, and select one causally motivated child action | Planning only | New immutable authorized child run |
| Plan TD, TS/IRC, restart, `formchk`, or `cubegen` | Use the dedicated recipe and retain `guard-not-supported` | Blocked locally | Separate authorized stages |
| Hand off a checkpoint or formatted wavefunction | Resolve each record role with `input-and-checkpoint-workflows.md` | Planning only | Hash-bound private consumer |
| Claim a result | Apply task-specific scientific gates and independent convergence evidence | No positive claim in development | Requires promoted evaluator and real fixtures |

## Real public entry points

After a licensed Unix environment is correctly set up, the public running page
documents these forms:

```text
g16 job-name
g16 < input-file > output-file
```

The first consumes `job-name.gjf` and produces `job-name.log`; the second binds
stdin/stdout explicitly. A redirected log can exist even when the provider fails, so
neither file existence nor a shell exit alone is the acceptance condition.

The public utility pages document:

```text
formchk [options] chkpt-file [formatted-file]
cubegen nprocs kind fchkfile cubefile npts format [cubefile2]
```

Use the exact argv shown in the selected recipe only after resolving the recipe's
first-party source, checking the installed revision's help on the licensed platform,
and recording authorization. Do not invent `g16 --version`: the registered revision
probe is the revision text in exact bound output plus a trusted private executable
record.

## Fail-closed handoff record

Before a provider command, require at least:

- exact provider/revision and platform evidence;
- license/entitlement attestation and one-action authorization;
- audited input hash/size and non-aliasing output paths;
- model chemistry, charge/multiplicity, structure, task and resource policy;
- checkpoint parent/output identities and scratch/retention policy.

After a command, keep process status, provider termination, requested task
completion, checkpoint identity and scientific acceptance as separate gates. A
normal termination means technical completion only.

## Typical acceptance paths

For a minimum candidate, the smallest documented path is an audited `Opt Freq` job,
optimization completion, frequencies from the same level/geometry, zero meaningful
imaginary modes, and independent convergence/model-chemistry justification. It does
not establish the global minimum or automatically validate thermochemistry.

For a transition-state candidate, use ordered QST2/QST3 structures or another
explicit TS method, then a same-level frequency calculation with exactly one intended
imaginary mode and an eigenvector matching the reaction coordinate, followed by both
IRC directions and independently identified endpoints. The current guard blocks this
entire path; the recipe is a reviewable specification, not support.

For checkpoint-derived files, bind `.chk -> .fchk -> .cube` as a hash lineage.
Conversion and visualization never create independent scientific evidence, and these
artifacts may contain sensitive molecular/electronic information.
