# LOBSTER 5.1.1 calling surfaces and end-to-end recipes

## Evidence state and hard boundary

The first-party download page identifies **LOBSTER 5.1.1**, dated 2024-09-26,
as the current 940 MB package and advertises projected COHP, COOP, and atom-
projected DOS from VASP, ABINIT, or Quantum ESPRESSO plane-wave output. It says
the manual and examples are inside the downloaded package. The package is gated
by a non-exclusive, non-transferable, revocable, non-profit-only license that
prohibits third-party access without written consent.

The public first-party pages do **not** specify the exact executable filename or
argv, complete `lobsterin` grammar, provider-specific required files/settings,
5.1.1 completion/fatal markers, or complete output schemas. Do not reconstruct
those details from memory, a community tutorial, LobsterPy, or an older manual.
Any native recipe lacking an authorized exact 5.1.1 manual/example identity is
`manual-required` and blocked.

On 2026-07-19, metadata-only probes found no `lobster`, `lobster-5.1.1`, or
`lobster-5.1.0` executable. No help/version command or native example was run.
The native-validation state is `native-not-run`.

## Safe discovery layer

The catalog helper reads static JSON and searches candidate executable names
with `PATH` metadata only. It does not launch LOBSTER or inspect private assets.

```bash
python3 -B skills/lobster-bonding-analysis/scripts/lobster_catalog.py groups
python3 -B skills/lobster-bonding-analysis/scripts/lobster_catalog.py search "projected COHP"
python3 -B skills/lobster-bonding-analysis/scripts/lobster_catalog.py show native.execution
python3 -B skills/lobster-bonding-analysis/scripts/lobster_catalog.py recipes
python3 -B skills/lobster-bonding-analysis/scripts/lobster_catalog.py plan recipe.native-run
python3 -B skills/lobster-bonding-analysis/scripts/lobster_catalog.py probe
```

`plan recipe.native-run`, the VASP native handoff, and every native COHP/COOP/DOS
recipe return exit `3` until exact authorized manual evidence is supplied. The
QE route additionally remains `design-only`. A detected binary is only
`available-unverified`; it is not authorization, version identity, adapter
maturity, or scientific evidence.

## End-to-end workflow

### 1. Establish authorization and provider identity

Record a privacy-safe entitlement receipt, exact binary hash/version evidence,
authorized manual/example identity, platform/build identity, and basis-resource
identity. Do not store the binary, manual, examples, basis contents,
registration data, personal information, credentials, or private paths in Git
or a report.

If the output says any version other than 5.1.1, the binary/manual/output
identities disagree, or the identity is absent, stop with
`LOB.VERSION.SOURCE_CONFLICT` or `LOB.PROVIDER.VERSION_UNSUPPORTED`.

### 2. Obtain a reviewed plane-wave parent

LOBSTER analysis begins after a self-consistent electronic wavefunction exists.
The parent calculation Skill, not LOBSTER, owns electronic-structure correctness.

For a VASP parent, require `vasp-rigorous-calculations` evidence for:

- one immutable structure, INCAR/settings, k-point sampling/weights, potential
  metadata, wavefunction, output, code/build, and task lineage;
- completion, electronic convergence, claim-relevant ENCUT/k-point/band
  convergence, spin/noncollinear/SOC state, occupations/smearing, and static-
  calculation identity;
- enough accurately represented bands for the projection/integration window;
- lawful VASP/POTCAR use, with no POTCAR bytes in this repository.

Do not guess the exact 5.1.1 file bundle or LOBSTER-specific VASP settings from
this guide. Compare the reviewed parent to the authorized 5.1.1 VASP chapter and
example, then bind every required byte by hash. A file named `WAVECAR` does not
prove parent eligibility.

For a QE parent, require the same scientific lineage from
`qe-rigorous-calculations`, plus exact authorized 5.1.1 evidence for supported QE
version, pseudopotential classes, wavefunction/save artifacts, conversion
settings, spin/SOC constraints, and invocation. The public LOBSTER page only
establishes that some QE route exists. This development Skill has no real QE
profile or forward fixture, so the route remains `design-only` and must not run.

ABINIT is likewise advertised but has no adapter here.

### 3. Review `lobsterin` against the authorized manual

Generate no native keyword from memory. A reviewer must record, without copying
restricted text:

- exact 5.1.1 manual/example hash and the relevant section/example identifier;
- parent-provider declaration and all required file/settings checks;
- basis-selection mode, basis resource identity, and per-element orbital list;
- requested observable: COHP, COOP, DOS, population/charge, k-dependent COHP,
  or another separately profiled task;
- atom-pair/orbital selectors, automatic-neighbor policy if any, spin/SOC mode,
  energy/projection/integration window, Fermi convention, and output options;
- overwrite/restart behavior, resource limits, and expected output set.

The execution record must bind the exact `lobsterin` bytes. Review success does
not imply that the chosen basis or interaction set is chemically adequate.

### 4. Native launch remains manual-required

The public first-party pages contain no exact launch command. Consequently this
Skill intentionally emits no executable argv. Only an authorized user may fill
an execution request from the exact 5.1.1 manual/binary, after which the shared
execution layer must use an argv array with no shell, fixed working directory,
resource limits, network policy, no silent overwrite, stdout/stderr capture, and
input/output hashes.

Never interpret process exit zero as completion. Validate the exact version-
matched completion/fatal markers and required artifacts from the authorized
manual/profile. Preserve failed output rather than merging it with a rerun.

### 5. Projection-quality gate

The official projection page explains that the plane-wave wavefunction is
reconstructed in a local auxiliary basis and that the spilling indicator ranges
from one to zero, lower being better. It does not define a universal pass value.

Require all of the following before analyzing curves:

- parser-observed basis agrees with the planned basis family/resource hash and
  per-element orbital list;
- absolute charge and total spilling values are present, finite, in the valid
  range, and below **predeclared, claim-specific** thresholds;
- projected-band coverage/fraction, projection energy window, Fermi reference,
  spin/SOC treatment, and warnings/band-overlap diagnostics are captured;
- basis alternatives and sensitivity are assessed when the scientific claim
  depends on orbital selection or when spilling/warnings are marginal.

Low spilling is necessary evidence, not proof that a basis is chemically
complete, uniquely appropriate, or adequate for every atom/orbital/energy
region. Never relax a threshold after seeing the result.

### 6. Observable gates

#### COHP

COHP partitions the one-particle band-structure energy into orbital-pair
interactions. Its integral hints toward interaction strength but is not the
total-energy bond dissociation energy. Preserve whether the raw quantity is COHP
or the commonly plotted `-COHP`; their signs are opposite.

Bind curve/list rows to atom and orbital selectors, spin channels, energy unit,
Fermi zero, integration window, and integral convention. Recompute or reconcile
stored integrals within a predeclared tolerance. Do not call an automatically
selected contact a chemical bond without expert review.

#### COOP

COOP partitions electron number, not band energy. Integrated COOP is an electron-
population-like quantity and cannot be substituted for ICOHP. Require the same
selector, sign, Fermi, energy-grid, spin, and integral evidence.

#### projected DOS

DOS shows where electronic states occur; it does not itself give bonding or
antibonding character. Preserve atom/orbital/spin labels, energy/Fermi reference,
normalization, and total-versus-projected semantics. Test closure/integration
only under an explicitly defined electron-count and projection convention.

#### population and charge

Method papers establish population/charge capability, but no automatic charge
partition is an oxidation-state proof. Preserve method, basis, spin, and parent
identity and require independent chemical review.

### 7. Declarative audit

After a trusted private parser/exporter has converted exact native artifacts to
the declared interchange and bound their hashes, run:

```bash
python3 -B skills/lobster-bonding-analysis/scripts/lobster_guard.py audit \
  --request request.json \
  --output lobster-audit-report.json
```

The current parser/fixtures are original synthetic formats. A passing report is
only local synthetic gate evidence; it is not proof of genuine 5.1.1 format
compatibility and carries `no_positive_claim`.

### 8. Postprocessing handoff

Only after authorization, parent, execution, basis, projection, artifact,
observable, and claim gates pass may a future adapter hand data to
`dft-postprocess`:

1. retain raw artifact hashes and exact parser/version identity;
2. normalize arrays without discarding atom/orbital selectors, spin channels,
   raw COHP versus `-COHP` convention, energy/Fermi reference, integration
   window, units, k-point/weight semantics, and projection-quality metrics;
3. record any interpolation, summation, spin aggregation, sign inversion, or
   energy shift as an explicit transformation;
4. produce provenance-bearing plots/tables and an artifact manifest;
5. keep scientific interpretation at `eligible_for_expert_review` at most.

`dft-postprocess` may parse, normalize, integrate, compare, and plot. It cannot
repair an ineligible parent, wrong basis, high/missing spilling, absent
interaction, truncated run, sign ambiguity, or non-comparable calculation.
This development route remains non-routable until separately activated.

## Optional LobsterPy companion route

Developer-authored LobsterPy documentation gives this postprocessing call shape
for already existing matching artifacts:

```bash
lobsterpy description \
  -fcharge CHARGE.lobster \
  -fcohp COHPCAR.lobster \
  -ficohp ICOHPLIST.lobster \
  -fstruct POSCAR.lobster \
  -fjson summary.json
```

Use matching `--coops` or `--cobis` flags only for corresponding files. Record
automatic cutoffs, cation/anion classification, orbital selection, and spin
aggregation. LobsterPy documentation is authority for LobsterPy calls and file
arguments only; it does not establish native LOBSTER input syntax, completion,
projection validity, or scientific acceptance. The companion was not installed
or run in this review.

## Comparative-claim gate

Before comparing ICOHP/ICOOP/COBI or curve features across structures, require:

- compatible provider/version, DFT method, potentials, spin/SOC, smearing,
  numerical convergence, and k-point sampling;
- comparable basis families/orbitals and accepted projection metrics;
- the same interaction definition, multiplicity/coordination treatment,
  orbital aggregation, energy/Fermi/integration window, and sign convention;
- a predeclared comparison set, uncertainty/sensitivity assessment, and no
  post-hoc omission of unfavorable contacts.

Even a technically comparable ICOHP trend is not automatically bond energy,
phase stability, oxidation state, causal mechanism, or experimental agreement.

## Low-reasoning decision table

Evaluate in order; stop at the first established row.

| Condition | Action | Claim ceiling |
|---|---|---|
| Native execution requested but exact authorized 5.1.1 manual/binary identity is absent | `manual-required`, exit `3`; request evidence | none |
| QE or ABINIT parent route requested | `design-only`, exit `3`; require a provider profile and real forward fixture | none |
| Provider/manual/output versions disagree or are unversioned | block version conflict | none |
| Parent receipt, wavefunction, structure, settings, potential, or execution hashes detach | block lineage | none |
| Completion/fatal profile or required artifact is absent | block task | none |
| Basis identity, charge/total spilling, band/window, Fermi, or warning evidence is missing/fails | block projection | none |
| Curve/list/DOS selector, sign, spin, unit, reference, grid, or integral semantics fail | block observable | none |
| Request asks automatic bond strength/order, oxidation state, stability, or causality | restrict to technical evidence; require expert review | none |
| All current synthetic guard gates pass | retain local report and seek lawful real-artifact validation | `no_positive_claim` |
| Evidence matches no row | fail closed | none |

The canonical machine route remains `weak-model-decision-table.json`. The
catalog query layer does not override it.

## Failure semantics summary

| Observation | State |
|---|---|
| Candidate executable absent | `unavailable`; do not install implicitly |
| Candidate executable found | `available-unverified`; do not run help/version automatically |
| Public feature exists but native grammar/argv absent | `manual-required`, blocked |
| Provider advertised but adapter/fixture absent | `design-only`, blocked |
| Scheduler/process success only | execution incomplete |
| Completion only | projection/task gates still pending |
| Low spilling only | basis and scientific gates still pending |
| Companion parser succeeds | postprocessor-readable only |
| All technical gates pass | at most expert-review eligibility, never automatic chemical truth |

Machine-readable details are in `software-capability-catalog.json`,
`task-recipes.json`, `official-sources.yaml`, and `version-matrix.yaml`.
