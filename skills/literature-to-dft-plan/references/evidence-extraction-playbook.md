# Literature evidence-extraction playbook

Use this playbook after lawful access to the source has been established externally. It guides content extraction and comparison; it does not retrieve or authenticate sources.

## Convert the research question into an extraction form

Define the target system, phase/structure, observable, method family, thermodynamic conditions, dimensionality, and intended decision. Then extract only information relevant to those fields.

For each source, record:

- stable identity, version/correction status, bounded locator, and exact content hash;
- structure and composition actually studied;
- code, method, functional, pseudopotential/basis, spin/SOC/charge, and corrections;
- numerical protocol: cutoffs, grids, cells, smearing, thresholds, sampling, and convergence evidence;
- observable definition, unit, normalization, reference convention, and uncertainty;
- author claim, supporting result, limitation, and whether the source itself labels an inference;
- applicability and mismatch relative to the current project.

## Keep five semantic classes separate

| Class | Example | Permitted use |
|---|---|---|
| source assertion | authors state a phase is stable | report as attributed claim |
| numerical fact | a value with unit and locator | compare after protocol checks |
| inference | a mechanism proposed from several results | create a testable hypothesis |
| project choice | selected functional or tolerance | record owner and rationale |
| new claim proposal | result the project may seek to support | define required evidence |

Never turn a source assertion into a project fact by removing attribution.

## Decide whether a published parameter transfers

Check, in order:

1. same structure, composition, dimensionality, charge, spin, and physical regime;
2. same code semantics and version-relevant behavior;
3. compatible functional, pseudopotential/basis, relativistic treatment, and corrections;
4. compatible cell, sampling, smearing, temperature, pressure, and reference convention;
5. source evidence that the parameter was converged for the target observable;
6. an independent convergence plan for the current project.

If any item fails, retain the published value as a starting hypothesis only. Official defaults and frequently copied parameters are not convergence evidence.

## Resolve conflicting literature

Build a comparison table before choosing a side. Look for differences in structure, method, observable definition, reference state, convergence, corrections, and data processing. Classify the conflict as direct contradiction, different regime, different definition, insufficient reporting, or unresolved. Preserve minority or negative evidence when it changes the planned test.

## Translate evidence into calculations

For each proposed calculation, specify:

- the source-backed question or discrepancy;
- the project assumption being tested;
- structure and code route;
- varied parameters and acceptance tolerance;
- expected output and postprocess route;
- result that would support, weaken, or leave the hypothesis unresolved;
- cost/risk and stop condition;
- human decisions required before execution.

Do not translate prose such as “dense k mesh” or “high cutoff” directly into input. Require a value, unit, context, and current-system convergence plan.

## Extract methods without copying text

Paraphrase the method at the level needed to reproduce or compare it. Store short bounded locators and structured values instead of article bodies. Keep quotations exceptional and within applicable copyright/redistribution limits.

## Operational heuristics

These are practitioner heuristics, not source-authenticated facts:

- Start from one evidence table rather than accumulating free-form notes.
- Extract limitations and negative results at the same time as headline values.
- Prefer sources with enough method detail to test comparability, not only high citation count.
- Treat supplementary information, corrections, and data repositories as versioned parts of the evidence chain.
- Recheck older workflows against the current code manual before converting them into inputs.
