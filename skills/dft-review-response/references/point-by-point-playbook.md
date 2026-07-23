# Point-by-point response playbook

Use this playbook to decide what each reviewer comment requires before drafting polished prose. It does not edit or submit a manuscript.

## Decompose every comment

Split compound comments into atomic requests. Classify each request as:

- clarification or missing definition;
- presentation, figure, table, or organization change;
- literature or attribution gap;
- method/reproducibility question;
- request for existing analysis;
- request for new calculation or experiment;
- challenge to interpretation or claim strength;
- scope disagreement or infeasible request.

Keep one traceable response and one change/no-change decision per atomic request.

## Choose the evidence route

| Request type | Minimum evidence before claiming resolution |
|---|---|
| clarification | exact manuscript location and verified replacement text |
| figure/table change | source dataset, regenerated artifact, and exact diff |
| literature | authenticated source evidence and citation placement |
| method detail | input/protocol evidence consistent with the actual run |
| existing analysis | accepted run plus validated postprocess artifact |
| new calculation | approved objective, active route, convergence plan, terminal run, and claim review |
| interpretation challenge | claim-evidence comparison including adverse evidence |
| disagreement | bounded scientific rationale and author decision |

A proposed change is not implemented until the exact manuscript diff or artifact proves it.

## Draft the response in five parts

1. State what aspect of the comment is being addressed without copying unnecessary reviewer text.
2. Give the evidence-bounded scientific answer.
3. State the exact manuscript/figure/table change or explain why no change is made.
4. Identify location and artifact/diff reference.
5. Preserve limitations, unresolved work, and any author decision still required.

Use a respectful tone, but do not use politeness to imply that unsupported work was completed.

## Handle a new-calculation request

Before promising work, identify the claim at stake, observable, method, acceptance tolerance, estimated cost, required parent artifacts, and decision deadline. Distinguish:

- required evidence for the manuscript's existing claim;
- useful but out-of-scope extension;
- infeasible request with a defensible alternative;
- request already answered by existing evidence.

If the current claim cannot survive without the requested evidence, weaken or remove the claim unless the new calculation is completed and accepted. Never promise a specific result.

## Handle disagreement or partial agreement

Map every disputed sentence to its evidence. Agree where the evidence warrants it, narrow overstatements, and explain retained conclusions with explicit limitations. A disagreement requires an author decision; the tool may assemble evidence but cannot take the scientific position for the authors.

## Verify before calling the package ready

- Every subcomment has exactly one status.
- Every claimed change has an exact diff/artifact reference.
- Every numerical statement matches the accepted dataset and units.
- New citations support the nearby statement and have valid source lineage.
- Figure/table numbering and cross-references are consistent.
- Response wording does not exceed the revised manuscript claim.
- Deferred and rejected work remains visible.
- Human authors have reviewed scientific meaning, tone, privacy, and submission scope.

## Operational heuristics

These are practitioner heuristics rather than journal policy:

- Build the comment-to-evidence matrix before drafting prose.
- Respond to the strongest scientific interpretation of a comment, not only its easiest wording.
- Prefer a narrow verified change over a broad promise.
- Track manuscript edits separately from response-letter prose; they can drift independently.
- Re-run citation, figure, and claim checks after the final manuscript merge.
