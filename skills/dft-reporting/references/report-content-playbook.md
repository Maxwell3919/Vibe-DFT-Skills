# Scientific report content playbook

Use this playbook to assemble a readable report from validated records. It does not establish scientific acceptance or publication authority.

## Start from claims, not figures

For every reportable statement, record:

1. the bounded claim and its claim ceiling;
2. the exact supporting evidence and record hashes;
3. method, structure, software, and protocol identity;
4. observable value, unit, uncertainty or convergence tolerance;
5. adverse findings and alternative explanations;
6. limitations and transferability boundary;
7. human decision status.

If a statement cannot be filled from accepted evidence, weaken it, mark it unresolved, or remove it.

## Assemble the report in evidence order

### Scope and question

State the system, scientific question, compared protocols, target observables, and what was not assessed. Avoid implying that the report covers tasks absent from the evidence bundle.

### Method and reproducibility

Include structure provenance, code/version, method choices, spin/SOC/charge state, pseudopotential or basis identity, convergence dimensions, workflow lineage, and the exact accepted production run. Separate official documentation from project choices and convergence evidence.

### Results

For each result, pair the numerical statement with the corresponding table/figure and source record. Report units and reference conventions, such as energy zero, cell normalization, per-atom/per-cell basis, broadening, q/k weights, or temperature/pressure.

### Validation and sensitivity

Show the convergence tail or sensitivity evidence that supports the chosen protocol. Describe state changes, unstable modes, fit residuals, finite-size effects, sampling uncertainty, or incompatible comparisons instead of hiding them in supplementary prose.

### Limitations and decision

Distinguish technical completion, numerical validity, physical interpretation, and human scientific acceptance. State the highest supported conclusion and the evidence needed to raise it.

## Figure and table checklist

- Bind every panel and table to an `artifact-manifest` entry and source dataset hash.
- Label axes, units, normalization, reference energies, paths, broadening, and transformations.
- Keep raw/normalized/derived data distinguishable.
- Explain selections and filters that change the visible result.
- Verify legend, color, symbol, and panel mappings against the data rather than visual memory.
- Do not crop away unstable, failed, or contradictory regions without disclosure.
- Treat a rendered image as a presentation artifact, not the numerical source of truth.

## Report negative or blocked results

Record the attempted protocol, decisive blocker, observed evidence, impact on the claim, and smallest next action. Do not describe an unfinished calculation as evidence of absence. Distinguish a physical instability from numerical, model, parser, and execution failures.

## Compare methods or materials

Require compatible structures, compositions, reference states, units, methods, sampling, and acceptance criteria. If one dimension differs, state it and limit the comparison. A visually aligned plot does not make unlike protocols comparable.

## Reproducibility appendix

Provide immutable identities for inputs, source manifests, run manifests, normalized datasets, artifact manifests, validation reports, software versions, and repository commits. Refer to restricted inputs by permitted metadata only; never embed licensed contents.

## Operational heuristics

These are practitioner heuristics rather than scientific acceptance rules:

- Draft the claim-evidence table before prose; unsupported sentences become obvious early.
- Keep one canonical numerical table per observable and generate plots from it.
- Record failed sensitivity checks beside the accepted check to prevent selective reporting.
- Use stable IDs in captions and notes so later figure revisions cannot silently change provenance.
- Let the report remain incomplete when evidence is incomplete; polished prose is not a gate.
