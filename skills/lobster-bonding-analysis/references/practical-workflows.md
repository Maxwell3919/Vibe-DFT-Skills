# LOBSTER practical setup, output, and interpretation playbook

## Contents

1. [Evidence layers](#evidence-layers)
2. [Parent-provider routes](#parent-provider-routes)
3. [VASP parent preparation](#vasp-parent-preparation)
4. [Basis and projection workflow](#basis-and-projection-workflow)
5. [`lobsterin` review map](#lobsterin-review-map)
6. [Output-role map](#output-role-map)
7. [Projection-quality acceptance](#projection-quality-acceptance)
8. [Observable-specific interpretation](#observable-specific-interpretation)
9. [Bond and interaction selection](#bond-and-interaction-selection)
10. [Operational heuristics](#operational-heuristics)
11. [Failure triage](#failure-triage)
12. [Minimum review record](#minimum-review-record)

## Evidence layers

Keep the following authorities separate:

- **provider fact**: the public LOBSTER site or the authorized exact-version
  manual establishes a feature, provider, syntax, or output;
- **method fact**: a primary COHP/LOBSTER/COBI paper establishes a definition
  or limitation;
- **adapter observation**: public pymatgen, LobsterPy, or atomate2
  documentation exposes a keyword, preparation pattern, parser field, or file
  role; this is useful operational evidence but not native LOBSTER 5.1.1 syntax
  authority;
- **operational heuristic**: a conservative practice from repeated
  plane-wave-to-local-orbital workflows, not a universal threshold;
- **native evidence**: an authorized, version-bound run whose parent, input,
  executable, transcript, output, basis, and projection metrics are hash-bound.

This public playbook intentionally supplies no launch command and no complete
runnable `lobsterin`. Before native execution, compare every observed keyword,
file role, and provider requirement against the authorized LOBSTER 5.1.1 manual
and shipped example, then record only privacy-safe identities and hashes.

## Parent-provider routes

The first-party download page advertises plane-wave parents from VASP, ABINIT,
and Quantum ESPRESSO. That is a capability statement, not a validated adapter.

| Parent | Public provider support | This Skill's state | Required next evidence |
|---|---|---|---|
| VASP | advertised; represented in primary LOBSTER papers | candidate fixture and public adapter observations only | authorized 5.1.1 file/settings chapter, exact VASP/version/potential compatibility, and legally reusable real forward fixtures |
| Quantum ESPRESSO | advertised | design-only | exact supported QE versions, pseudopotential classes, save/wavefunction/conversion contract, spin/SOC constraints, and real fixtures |
| ABINIT | advertised | design-only | exact supported versions, wavefunction/conversion contract, settings, and real fixtures |

Never carry a VASP assumption into QE or ABINIT. A software name, directory
name, `WAVECAR`-like file, or completed scheduler job is not a parent contract.

## VASP parent preparation

### Scientific parent gate

Call `vasp-rigorous-calculations` first and require one immutable static
electronic-structure lineage:

- final structure, species/site order, k points and weights, functional,
  privacy-safe PAW potential identities, spin/noncollinear/SOC state,
  occupations, smearing, charge state, and symmetry;
- exact VASP build and hashes for the input set, wavefunction, structured
  output, and completion evidence;
- electronic convergence and claim-specific convergence in cutoff, k mesh,
  number of bands, occupations, and the energy range to be projected;
- an explicit distinction between a relaxation, a charge-density continuation,
  a band-path calculation, and the static parent actually consumed by LOBSTER.

The official FAQ says an electronic-structure calculation must precede the
bonding extraction. LOBSTER cannot repair an unconverged or scientifically
unsuitable parent.

### Public adapter observations

Current public pymatgen documentation exposes a VASP preparation helper that:

- reads `POSCAR`, `INCAR`, optional `POTCAR`, and `vasprun.xml` to construct a
  `Lobsterin` object;
- can enumerate possible basis combinations from minimum/maximum basis
  resources and privacy-safe POTCAR symbols;
- prepares a static VASP input with `LWAVE=True`, inserts `NBANDS`, and uses
  `ISYM=0` or `-1`, while explicitly warning that the remaining settings still
  require review;
- provides a gamma-centered explicit-k-point writer and a standard-primitive
  structure writer for band-path use.

Treat these as adapter observations, not provider defaults. In particular:

- never read, copy, log, or commit POTCAR content; use approved metadata and
  hashes outside reports;
- do not change `ISYM`, k points, primitive-cell representation, or `NBANDS`
  without invalidating the old wavefunction lineage and rerunning VASP;
- compare the exact parent bundle required by the authorized 5.1.1 manual
  before launch; the helper's preparation inputs are not automatically the
  native runtime bundle;
- verify that explicit k-point weights and spin/SOC settings match the intended
  projection and observable.

## Basis and projection workflow

### 1. Pin the basis identity before the parent run

Record:

- exact LOBSTER version and basis-family/resource identity;
- privacy-safe PAW potential label for each element, in structure order;
- planned orbital list for each element and the rationale for including
  semicore, valence, polarization, or target unoccupied orbitals;
- number of local basis functions and the resulting parent `NBANDS`
  requirement from the authorized provider instructions;
- target projection/analysis energy window and the bands that span it.

Do not choose orbitals solely after inspecting the desired COHP curve. Basis
selection is part of the analysis plan.

### 2. Enumerate defensible candidates

Public pymatgen/LobsterPy workflows can enumerate minimum-to-maximum basis
combinations for compatible VASP potential symbols. Use that feature only as a
candidate generator. The automated-workflow paper used a particular
`pbeVASPfit2015`/VASP setup; it does not establish a universal family for every
functional, potential release, element, pressure, oxidation state, or LOBSTER
version.

For each candidate, verify against the authorized 5.1.1 basis resources:

- every element is covered exactly once;
- the basis is compatible with the actual potential identity;
- occupied states and all claim-relevant unoccupied/semicore states are
  represented;
- the parent has enough bands and the projection window lies within its
  trustworthy eigenvalue range.

### 3. Run a predeclared basis pilot

When more than one chemically plausible basis exists, compare them on the same
parent with a predeclared decision rule. Retain, per basis:

- absolute charge spilling and absolute total spilling by spin channel;
- projected-band coverage/fraction and all band-overlap, orthonormality,
  linear-dependence, or excessive-band warnings;
- basis observed in `lobsterout` versus the planned per-element orbital map;
- stability of the requested COHP/COOP/COBI/DOS features in the declared
  energy window;
- resource cost and whether output truncation or memory pressure occurred.

Prefer a chemically justified basis that passes all projection and stability
gates. The numerically lowest single spilling value does not automatically win;
an enlarged basis can alter linear dependence, band coverage, and the meaning
of orbital-resolved comparisons.

### 4. Freeze the selected basis

Hash the selected `lobsterin`, record the basis family/resource receipt and
per-element orbitals, and bind them to the parent validation receipt. Any basis,
energy-window, structure, potential, band-count, k-point, spin, or SOC change
creates a new analysis lineage.

## `lobsterin` review map

The following names are visible in current public pymatgen adapter
documentation. They are an **adapter-observed vocabulary**, not a complete or
version-guaranteed LOBSTER 5.1.1 grammar. Confirm exact spelling, value syntax,
defaults, interactions, and availability in the authorized manual.

| Field family | Adapter-observed names | Review question |
|---|---|---|
| basis | `basisSet`, `basisfunctions`, `useRecommendedBasisFunctions`, `customSTOforAtom` | Which exact resource and per-element orbitals are used, and do they match the parent potentials and observed output? |
| energy/grid | `COHPstartEnergy`, `COHPendEnergy`, `COHPSteps`, `gaussianSmearingWidth`, `forceEnergyRange` | Does the window cover the scientific question and remain inside the parent/projection range? Are grid and broadening recorded? |
| interaction selection | `cohpGenerator`, `cohpbetween`, `cobiBetween`, `kSpaceCOHP` | Which periodic atom/image/orbital interactions are included, and is the selector complete for the claim? |
| projection diagnostics | `bandwiseSpilling`, `kpointwiseSpilling`, `printTotalSpilling`, `doNotUseAbsoluteSpilling` | Are absolute charge/total spilling and localized diagnostics retained without disabling the quality gate? |
| output controls | `skipcohp`, `skipcoop`, `skipcobi`, `skipdos`, `skipGrossPopulation`, `skipPopulationAnalysis`, `skipMadelungEnergy`, `createFatband` | Does the requested artifact set match the analysis plan, and are skipped products intentional? |
| projection reuse | `saveProjectionToFile`, `loadProjectionFromFile` | Is reuse authorized by the exact version and hash-bound to an unchanged parent, basis, and input? |
| advanced matrices/real space | `writeMatricesToFile`, `realspaceHamiltonian`, `realspaceOverlap`, wavefunction-print fields | Is the large/specialized output necessary, bounded, and covered by a validated parser? |

Do not enable a `doNot*`, `skip*`, projection-reuse, or advanced-output option
to bypass a failed gate. Do not infer default output production merely because
a public parser knows a filename.

## Output-role map

Public pymatgen, LobsterPy, and atomate2 documentation expose these common file
roles. The list is operationally useful but is not a complete 5.1.1 schema.
Require the exact manual and genuine output before parser promotion.

| Role | Adapter-observed files | Required interpretation evidence |
|---|---|---|
| run log and projection audit | `lobsterout` (and workflow-captured stdout such as `lobster.out`) | version/provider, parent code, completion/fatal markers, basis, charge/total spilling by spin, warnings, timings, and declared output presence |
| provider-neutral structure | `POSCAR.lobster` | structure hash, atom/site mapping, cell, provider lineage; LobsterPy documents default generation for LOBSTER 5.0+ but manual confirmation is still required for the exact run |
| COHP | `COHPCAR.lobster`, `ICOHPLIST.lobster` | pair/image/orbital labels, bond length, spin, energy/Fermi reference, raw COHP versus plotted `-COHP`, and integral window |
| COOP | `COOPCAR.lobster`, `ICOOPLIST.lobster` | same mapping plus electron-population rather than energy semantics |
| COBI | `COBICAR.lobster`, `ICOBILIST.lobster` | two-/multi-center definition, labels, spin, energy/reference, integration window, and bond-index interpretation boundary |
| projected DOS | `DOSCAR.lobster`, optionally `DOSCAR.LSO.lobster` | atom/orbital/spin labels, normalization, energy grid, Fermi zero, total/projected semantics, and closure test |
| populations and charges | `GROSSPOP.lobster`, `CHARGE.lobster` | Mulliken versus Loewdin method, basis, spin, atom mapping, charge sum, and uncertainty/sensitivity |
| electrostatics | `SitePotentials.lobster`, `MadelungEnergies.lobster` | Mulliken/Loewdin partition, Ewald convention, units, charge neutrality, and model limitations |
| projection diagnostics/reuse | `projectionData.lobster`, `bandOverlaps.lobster` | exact parent/basis hash, compatible version, band/k-point/spin mapping, and warning interpretation |
| distribution/advanced products | `BWDF.lobster`, `BWDFCOHP.lobster`, matrix or LCFO/MOFE products | task-specific schema and primary method evidence; remain outside the current guard |

Never pair a curve file with an integrated list, charge file, or structure from
another run because the filenames look conventional. Hash-bind the whole set.

## Projection-quality acceptance

The official projection page explains that spilling ranges from one to zero and
lower is better. It does not publish a universal pass value. Require:

1. exact basis-resource and per-element orbital agreement between plan and
   `lobsterout`;
2. finite absolute charge and total spilling for every spin channel;
3. thresholds declared before seeing the result and justified for the claim;
4. projected-band/window coverage and a Fermi reference consistent with every
   requested artifact;
5. review of band-overlap, orthonormality, linear-dependence, excessive-band,
   unsupported-feature, and truncation warnings;
6. basis/window sensitivity when the conclusion is orbital-specific or when
   diagnostics are marginal;
7. task-specific curve/list/DOS consistency after the projection gate.

Do not adopt a community workflow's `5%` (or any other number) as a universal
LOBSTER criterion. Report both the measured value and the predeclared limit.
Low spilling is necessary technical evidence, not proof of unique orbitals,
correct bonding, accurate total energy, or a chemical mechanism.

## Observable-specific interpretation

### COHP and ICOHP

COHP partitions one-particle band-structure energy by interaction. The official
FAQ warns that integrated COHP only hints toward bond strength and is not a
total-energy bond dissociation energy. Preserve the raw sign convention:
`COHP` and the commonly plotted `-COHP` have opposite signs.

Require atom/image/orbital selector, distance, multiplicity, spin channel,
energy unit, Fermi reference, integration window, and curve/list consistency.
Never rank structures by ICOHP unless parent method, basis, selector,
coordination/multiplicity, and window are comparable.

### COOP and ICOOP

COOP partitions electron number, not band energy. Its integral is
electron-population-like and cannot be substituted for ICOHP. Preserve the
native sign convention, spin, selector, window, and overlap-basis dependence.

### COBI and ICOBI

The 2021 primary paper introduces COBI as a solid-state bond-index descriptor
and relates its integrated value to a covalent bond-order concept. This does
not make every ICOBI a unique experimental bond order. Preserve whether the
quantity is two-center or multi-center, basis/orthogonalization convention,
spin, selector, energy window, and comparability. Ionic, metallic,
multi-center, delocalized, or highly coordinated systems need expert chemical
interpretation.

### Projected DOS

DOS locates states; it does not label bonding versus antibonding by itself.
Retain atom/orbital/spin labels, units, normalization per cell/atom/spin,
energy grid, smearing/broadening, and Fermi zero. Evaluate projected-to-total
closure only under an explicit convention and in the valid projection window.

### Mulliken/Loewdin populations and charges

`CHARGE.lobster` and `GROSSPOP.lobster` are basis-partitioned quantities.
Record method and basis and check atom mapping and charge sum. Differences
between Mulliken and Loewdin values are sensitivity evidence, not an error to
hide. Neither value alone proves a formal oxidation state, Bader charge,
charge transfer mechanism, or ionicity.

### Site potentials and Madelung energies

Preserve the partitioning scheme, Ewald convention, charge neutrality, units,
and structure. These quantities are model-dependent electrostatic descriptors;
they do not by themselves establish stability or a unique decomposition of the
DFT total energy.

## Bond and interaction selection

### Plan the interaction set before the run

Choose one or combine several predeclared strategies:

- explicit chemically motivated atom/image pairs and orbitals;
- symmetry-complete representatives plus multiplicities;
- an automatic distance-based generator broad enough to include all candidate
  contacts in a declared interval;
- a structure-graph/coordination policy whose method, cutoff, and charge
  source are recorded.

For every selected interaction retain atom indices, species, translation/image,
distance, orbitals, multiplicity, and the reason it belongs in the claim set.
Use structure visualization only as a mapping check, not as proof of bonding.

### Avoid selection bias

LobsterPy documents automatic filtering relative to the strongest integrated
interaction and defaults oriented toward cation-anion analysis. These are
postprocessing choices, not native LOBSTER completeness or universal chemistry.
The companion also warns that it can analyze only interactions that the
LOBSTER calculation included.

Therefore:

- generate a sufficiently broad native interaction set before applying a
  postprocessing cutoff;
- record `all bonds` versus cation-anion policy, charge method, relative
  cutoff, absolute noise cutoff, orbital cutoff, and spin summation;
- inspect omitted same-sign, anion-anion, cation-cation, long, weak, or
  antibonding contacts when they matter to the hypothesis;
- use different noise scales for ICOHP, ICOOP, and ICOBI only when justified;
  never reuse a numeric cutoff across different units by habit;
- retain the unfiltered list so a later reviewer can audit post-hoc omission.

## Operational heuristics

These practices are experience-layer guidance, not provider defaults:

- stage the immutable VASP parent read-only and run each basis/selector variant
  in a separate scratch directory; never merge failed and rerun outputs;
- start with a projection-quality pilot before requesting every large
  curve/matrix/fat-band artifact;
- use the smallest scientifically sufficient interaction set for exploratory
  runs, then widen it before any comparative or publication claim;
- preserve raw spin channels and raw COHP signs; perform summation, sign
  inversion, smoothing, and Fermi shifts only as explicit derived transforms;
- compare basis candidates and energy windows using the same parent; changing
  both at once prevents attribution;
- treat warnings in `lobsterout` as structured evidence. Do not accept the run
  because expected files exist;
- predeclare whether comparisons use per-bond, multiplicity-weighted,
  per-atom, per-formula-unit, or cell-summed quantities;
- use a coarse discovery run only to refine a final predeclared protocol, then
  rerun and validate the final analysis without silently carrying exploratory
  cutoffs.

## Failure triage

| Symptom | Likely cause | Required action |
|---|---|---|
| provider/version cannot be established | unversioned binary/output or detached manual | block native use and bind executable, entitlement, manual, and output header |
| parent is rejected or wavefunction cannot be read | wrong VASP/provider version, incomplete/static mismatch, file corruption, or unsupported settings | compare the authorized provider contract and parent hashes; rerun the parent rather than renaming files |
| band count/basis error | `NBANDS` inconsistent with selected basis or target window | regenerate the VASP parent from the frozen basis plan; do not edit metadata after the fact |
| high or missing charge/total spilling | unsuitable/incomplete basis, parent mismatch, window problem, or parse/version drift | review per-element orbitals, potential compatibility, band coverage, warnings, and alternative bases |
| low spilling but unstable curves | basis sensitivity, local orbital incompleteness, different windows/selectors, or numerical parent issue | compare predeclared bases/windows and parent convergence; keep the claim blocked |
| band-overlap/orthonormality warning | projection/basis/k-point problem or linear dependence | consult the exact manual, inspect localized diagnostics, and do not waive the warning from a low average spilling value |
| expected COHP/COOP/COBI pair absent | selector/generator excluded it, periodic image mismatch, or output skipped | inspect `lobsterin`, full list, translation, cutoff, and output controls; postprocessors cannot reconstruct an uncomputed pair |
| curve and integrated list disagree | mixed run, Fermi/window/sign/spin mismatch, parser version, or numerical integration convention | hash-bind matching artifacts and reconcile the declared convention before plotting |
| spin-polarized values appear doubled/halved | silent channel summation or normalization mismatch | retain raw channels, state the aggregation, and rerun derived normalization checks |
| charges do not match a formal oxidation model | basis-partition sensitivity or the formal model is inapplicable | report Mulliken/Loewdin values and sensitivity; do not coerce them into integer oxidation states |
| postprocessor produces a polished narrative despite failed gates | automation exceeded the evidence | discard the positive language; retain technical findings at `no_positive_claim` and request expert review |

## Minimum review record

Before a result can become `eligible_for_expert_review`, retain:

1. provider/version/license receipt identities with no licensed bytes or
   personal data;
2. accepted parent record and validation receipt hashes;
3. exact structure, k-point, potential-metadata, spin/SOC, band, window, and
   wavefunction identities;
4. `lobsterin` hash, basis family/resource identity, per-element orbitals, and
   interaction selectors;
5. execution record, exact manual/profile identity, completion/fatal evidence,
   and output hashes;
6. charge and total spilling, band/window/Fermi evidence, all warnings, and
   basis/window sensitivity;
7. task-specific file mapping, units, sign, spin, normalization, selector, and
   integral/closure checks;
8. every transformation used for plotting or comparison;
9. limitations and alternative explanations;
10. a claim that does not exceed the technical evidence.

The current development guard cannot produce this state from genuine 5.1.1
artifacts. Its synthetic pass remains `no_positive_claim`.
