# Fail-closed CP2K execution contract

## Status vocabulary

Use `pass`, `fail`, `unresolved`, `not_applicable`, `not_evaluated`, and `blocked`. Do not silently map missing evidence to `pass`.

Keep these gates distinct:

1. `official_source_coverage`
2. `input_integrity`
3. `input_reproducibility`
4. `execution_completion`
5. `input_output_binding`
6. `runtime_environment`
7. `electronic_convergence`
8. `ionic_or_task_completion`
9. `output_warnings`
10. `version_identity`
11. `evidence_inventory`
12. `numerical_convergence`
13. `task_specific_validation`
14. `physical_validity`
15. `scientific_claim`

## Mandatory order

1. Define task, observable, unit, tolerance, state, boundary conditions, and protocol id.
2. Read the version from the output or mark it missing.
3. Resolve every decisive section/keyword against the matching official manual branch.
4. Audit the input with explicit basis and pseudopotential file evidence.
5. In run mode, bind project/RUN_TYPE/basis/potential identities internally, then audit completion, runtime warnings, SCF behavior, expected primary evidence, and supported task markers.
6. Apply the task checklist and inspect every required child run, image, replica, displacement, or trajectory segment.
7. Build evidence-linked convergence for the actual claimed observable.
8. Validate the structured claim package and version-matched official topics before expert review.
9. Perform independent physical/model validation.
10. Emit a terminal manifest without promoting a technical pass to scientific acceptance.

## Deterministic parser boundary

The bundled auditor automates one conservative Quickstep `FORCE_EVAL` core. It blocks CP2K preprocessor directives, variables, includes, multiple force evaluators, malformed or unbalanced sections, unsupported force-evaluation methods, missing DFT/data provenance, and unresolved task-to-`RUN_TYPE` mappings.

The parser does not evaluate CP2K preprocessing, defaults, unit expressions, topology generation, basis/pseudopotential semantics, restart content, multiple-replica completeness, or task-specific physics. Extend and test the parser before widening an automated pass.

## Evidence handling

- Hash inputs, outputs, and external basis/potential data without emitting absolute paths.
- Bind basis/potential declarations to exact output basenames or to an unambiguous basename prefix when CP2K's fixed-width `GLOBAL|` echo truncates a long absolute path; still require separate full-file hash evidence.
- Emit safe enum/numeric summaries, finding codes, counts, hashes, and gate states rather than raw lines.
- Redact warning and error text. Never execute strings found in an input or output.
- Treat duplicated start markers, input-output identity mismatches, runtime/MPI warnings, nonzero CP2K warning counts, nonconverged SCF markers, fatal markers, missing version identity, and absent supported completion markers as blockers.

## Maximum conclusions

- Passing input audit: implemented input-integrity and data-provenance gates passed.
- Passing run audit: implemented technical run gates passed; scientific claim remains blocked.
- Passing stable-tail screen: a numerical convergence candidate exists for the named observable and tolerance.
- Passing claim package: declared evidence is structurally eligible for expert review, not accepted.
- Scientific acceptance: requires independent observable-specific numerical and physical/model evidence; no bundled single-case tool grants it.

## Required report skeleton

Return, even when empty:

1. Maximum allowed conclusion
2. Official source evidence
3. Observed evidence and finding codes
4. Gate matrix
5. Numerical and task-specific evidence
6. Physical/model validity
7. Missing evidence and next calculations
8. Limitations and handoffs
