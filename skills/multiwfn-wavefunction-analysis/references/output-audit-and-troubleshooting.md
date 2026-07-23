# Output audit, batch safety, and troubleshooting

Use this reference after selecting an eligible source and a manual-grounded
recipe. It combines official batch/runtime guidance with explicit operational
gates. It does not authorize executing Multiwfn.

## Contents

1. Acceptance layers
2. Private run directory and identities
3. Command streams and prompt sentinels
4. EOF and exit-status handling
5. Artifact audits
6. Failure taxonomy and troubleshooting
7. Version-sensitive behavior
8. Final status

## Keep five acceptance layers separate

| Layer | Question | Minimum evidence |
|---|---|---|
| Source eligibility | Does the input contain the information the task requires? | producer/export lineage, format semantics, hash, atom/electron/orbital/grid checks |
| Invocation correctness | Did the intended binary, settings, and prompt path run? | banner/update date, executable/settings hash, exact stdin, complete stdout/stderr, prompt sentinels |
| Artifact completion | Were fresh expected outputs created and parsed? | pre-run absence, nonempty files, hashes, dimensions/schema, transcript linkage |
| Numerical/physical validity | Are conservation, convergence, and method assumptions satisfied? | observable-specific closure, refinement/sensitivity, finite values, applicable source quality |
| Scientific acceptance | Does the evidence support the stated claim? | compatible controls/references, uncertainty/limitations, claim bounded to the descriptor |

Passing an earlier layer never implies a later one. An exit code, `q`, plotted
surface, or nonempty table is not a scientific acceptance criterion.

## Construct a private run directory

Use one fresh directory per source/task/state. Before a future authorized run,
create a manifest and verify that no expected fixed-name artifact exists.

Recommended private layout:

```text
run-id/
  manifest.yaml
  input/                 # symlink or immutable copy with hash
  commands.in
  multiwfn.stdout
  multiwfn.stderr
  artifacts/
  checks/
```

Do not commit real wavefunctions, structures, outputs, account names, or local
paths to this repository. Copy or move an output into `artifacts/` only after
the run finishes; preserve its original filename in the manifest.

The pinned manual contains batch examples that reuse fixed filenames such as
`ELF.cub`. **Operational gate:** do not reproduce that reuse across inputs in a
shared directory. Use isolated scratch directories, verify pre-run absence,
and never accept a file solely because it has the expected name.

## Freeze identity before execution

Record:

- distribution source, package SHA-256, executable SHA-256, platform and
  architecture;
- exact banner/update date and full versus noGUI build;
- `settings.ini` path or safe identifier, SHA-256, and discovery route;
- `-nt`, `-uf`, `-set`, `-silent`, environment, OpenMP stack, process stack,
  shared-memory, and thread settings relevant to the task;
- each converter/viewer/external code with separate version/hash/authorization;
- source and command-stream SHA-256 and bytes;
- current working directory and expected output allowlist in a private log,
  redacting sensitive absolute paths from portable reports.

**Manual fact:** command-line options may not take effect if `settings.ini`
cannot be located. Confirm the effective configuration from the transcript;
the command text is not evidence that the option was honored.

The full Linux build and Linux noGUI build have different capability surfaces.
noGUI cannot satisfy steps that require graphical windows or graph-related
functions. A community macOS build is not equivalent to the official current
Linux/Windows distribution without exact build provenance, banner identity,
and regression evidence.

## Build command streams from prompts, not menu titles

For an established silent-mode route, keep one exact response per line:

```text
Multiwfn <input-file> -silent < commands.in \
  > multiwfn.stdout 2> multiwfn.stderr
```

Do not generate `commands.in` by concatenating main and subfunction numbers.
First establish every intervening prompt, default, unit, atom/orbital/state
selection, export response, filename, return token, and main-menu exit against
the exact binary.

`q` is safe only at a confirmed main-menu prompt. Inside another selector it
can be data or an invalid choice. If a route includes a GUI close action, file
chooser, plot window, or manual inspection, classify it as interactive until a
separate non-GUI path is established.

The current catalog labels only the manual's orbital-composition and ELF
examples as documented stdin streams. Other entries are interactive prefixes
or GUI/tutorial workflows even when their early menu numbers are known.

## Use prompt sentinels

A validated adapter should match ordered, version-specific transcript
sentinels rather than only the final filename. At minimum check:

1. exact program/version banner;
2. source basename and detected format;
3. atom, basis/GTF, orbital/electron, spin, cell, or grid inventory required by
   the task;
4. main function and subfunction labels;
5. every parameter/selection prompt in order;
6. explicit computation/export completion text;
7. return to the expected menu and an intentional main-menu exit;
8. absence of fatal or ambiguity markers in both stdout and stderr.

Prompt text can change between updates. On drift, stop and capture a private
interactive transcript; do not keep feeding old answers in hope that the
artifact will be usable.

## Interpret EOF and exit status conservatively

The official manual notes that an EOF-related Fortran runtime message can occur
after a complete redirected input stream and may not by itself indicate failed
analysis. This repository intentionally treats it as ambiguous.

When EOF/runtime text appears:

1. locate the last confirmed prompt and response;
2. determine whether the task and export completed before EOF;
3. check whether an explicit `q` was supplied at the main menu;
4. scan earlier stdout/stderr for input, allocation, convergence, parser, or
   external-program failures;
5. validate every expected artifact from content, not existence;
6. classify `technical_complete_with_exit_anomaly` only if the exact adapter
   contract permits it; otherwise fail closed.

Never overwrite or discard stderr merely to obtain a zero-like presentation.

## Audit artifacts by type

### Cube or other grid

Require:

- nonzero bytes, parsable header, finite axes/counts/values;
- origin, axis vectors, counts, coordinate/value units, atom list and cell;
- expected field/channel and source electron/core convention;
- min/max, nonfinite count, integral where meaningful, and boundary/truncation
  inspection;
- pre-run absence and a new SHA-256 linked to the transcript;
- convergence under box/spacing refinement for quantitative use.

### Atomic or orbital table

Require:

- exact schema/column labels and units/dimensionless convention;
- atom/orbital count and order matching the source;
- finite values and no silently omitted rows;
- charge, electron, spin, population, projected-weight, or other relevant
  closure with residual;
- raw table preserved before normalization or parsing.

### Critical-point/path inventory

Require:

- critical-point coordinates, type, Hessian eigenvalues, gradient residual;
- search settings and starting-point source;
- duplicate policy, connected nuclei/path endpoints, and topology closure;
- numerical stability under stricter search/refinement.

### DOS or spectrum

Require:

- raw discrete levels/transitions and exact units;
- parsed count/spot checks against producer output;
- broadening, FWHM, scaling, energy reference, temperature and weights;
- numerical curve separate from rendering;
- parameter-sensitivity and method/parser version boundary.

### Excitation grids/descriptors

Require:

- matching-source proof and coefficient normalization/completeness;
- state/spin identity and grid metadata;
- hole/electron integrals near their defined target and transition-density
  closure where applicable;
- convergence with coefficient threshold, box, and spacing.

## Failure taxonomy

Use one primary failure code and retain the original output:

| Code | Meaning | Example |
|---|---|---|
| `SOURCE_INELIGIBLE` | required information absent or unverified | `.wfx` supplied for Mayer basis-space order |
| `SOURCE_IDENTITY_MISMATCH` | source does not match producer or paired file | excitation output and checkpoint have different geometry |
| `CONVERTER_UNVERIFIED` | external conversion lacks version/semantic checks | direct `.chk` route with unknown `formchk` |
| `VERSION_DRIFT` | banner/manual/recipe profile mismatch | prompt text differs from validated update |
| `SETTINGS_NOT_APPLIED` | configuration discovery/effect is uncertain | `-nt` present but settings failure appears |
| `GUI_CAPABILITY_MISMATCH` | route needs graph/GUI but build cannot supply it | topology GUI sequence on noGUI build |
| `PROMPT_DRIFT` | ordered menu/prompt sentinel differs | old stream reaches a different selector |
| `UNESTABLISHED_RECIPE` | only a function listing or prefix exists | inferred batch stream after `7,15,1` |
| `EXTERNAL_EXECUTION_BLOCKED` | route attempts an unauthorized converter/code | Hirshfeld-I tries to invoke Gaussian |
| `OUTPUT_COLLISION` | expected artifact existed before run | stale `ELF.cub` in work directory |
| `ARTIFACT_MISSING_OR_INVALID` | file absent, empty, stale, unparsable, or nonfinite | zero-byte cube after apparent completion |
| `NUMERICAL_CLOSURE_FAILED` | conservation/normalization check fails | hole integral far from one |
| `CONVERGENCE_NOT_ESTABLISHED` | grid/search/iteration/basis sensitivity unresolved | CP inventory changes with search refinement |
| `METHOD_INAPPLICABLE` | analysis assumptions do not cover source/task | unsupported excitation method parsed heuristically |
| `INTERPRETATION_OVERREACH` | claim exceeds descriptor evidence | BCP treated as proof of energetic stabilization |

Do not collapse these to `Multiwfn failed`; the remediation and evidence layer
are different.

## Symptom-driven troubleshooting

| Symptom | Check in order |
|---|---|
| Input rejected or atom/orbital count wrong | suffix and internal format; file completeness; producer dialect; converter stdout/stderr; spherical/Cartesian basis order; ECP convention |
| Immediate crash or allocation error | exact platform/build; dependencies; memory; thread count; `OMP_STACKSIZE`; process stack; shared memory; corrupted input; official known-fix history |
| Menu answers no longer align | banner/update date; manual profile; locale; full/noGUI build; preceding defaults/prompts; source family causing a different branch |
| Calculation runs but no expected file | export prompt/answer; current directory; fixed filename; permission/disk; earlier warning; GUI-only action; stale stream ended before export |
| Result differs across machines | executable/settings hashes; version date; compiler/build; thread/numerical settings; source/converter hashes; locale; grid/search settings |
| Result differs from another program | mathematical definition/sign/unit; source orbital/density/core convention; partition; grid; broadening; method/version |
| Output looks plausible but closure fails | treat closure as primary evidence; inspect truncation, missing coefficients/EDF, mapping, parser completeness, convergence |

The official quick-start document identifies wrong format, incomplete files,
incorrect menu responses, resource/stack configuration, NBO-plus-diffuse-basis
issues, and software defects among common failure classes. Reduce any suspected
defect to a minimal, privacy-safe reproducer before consulting the official
forum or authors. Do not post unpublished structures, licensed data, private
paths, or credentials.

## Record known version-sensitive behavior

Consult the official update history before treating a discrepancy as chemistry.
Examples relevant to the current manual profile include:

- the `2026.7.15` periodic free-volume grid correction;
- the `2026.3.18` CP2K Raman parsing correction;
- the `2026.3.11` DOS fragment-selection `cond` correction;
- the `2026.1.12` main-function-4 color-transition correction;
- the older IGM/IGMH formula change that makes results across that boundary
  non-identical.

These are examples, not a complete errata list. Record the exact program date
and search the official history for the selected function, input producer, and
symptom.

## Close a run with explicit status

Use a status object equivalent to:

```yaml
source_eligible: true
invocation_verified: true
artifact_complete: true
numerical_validity: false
scientific_acceptance: blocked
blocking_reasons:
  - grid refinement changes the reported integral beyond tolerance
known_limitations:
  - valence-only ECP density without EDF
```

Never summarize that state as `completed successfully`. State the highest layer
actually passed and the next evidence needed.

The deterministic `multiwfn_guard.py` covers only its documented source,
inventory-transcript, and controlled charge-table contracts. It does not parse
general Multiwfn output or establish any of the observable-specific checks in
this reference.
