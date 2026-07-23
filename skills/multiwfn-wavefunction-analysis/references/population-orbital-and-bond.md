# Population, charges, orbital composition, and bond descriptors

This reference turns Multiwfn manual sections 3.9, 3.10, 3.11, 3.15, 3.16,
3.19, and 3.25 into task checks. The methods below are alternative partitions
or descriptors. None is a unique observable, formal oxidation state, or
self-sufficient proof of bonding.

## Contents

1. Select and audit charge methods
2. Apply method-specific gates
3. Audit orbital composition
4. Audit bond-order routes
5. Analyze localized orbitals and fragments
6. Produce auditable tables
7. Diagnose common failures

## Select a charge method from its purpose

Start by stating why charges are needed: qualitative polarization, comparison
within a controlled series, force-field electrostatics, dipole reproduction,
reactivity descriptors, or QTAIM basin analysis. Do not choose a method solely
because it is available in main function 7.

| Method family | Source requirement | What to preserve | Main limitation |
|---|---|---|---|
| Mulliken | basis-function-bearing wavefunction | basis/ECP, overlap convention, spin populations, atom/basis order | strongly basis dependent; diffuse functions can yield nonphysical-looking populations |
| Lowdin | basis-function-bearing wavefunction | orthogonalization convention, basis/ECP, spin treatment | still basis and orthogonalization dependent |
| Hirshfeld | density/GTF data and free-atom reference densities | atomic reference/radial grid, integration settings, raw and normalized sums | often small charge magnitudes; not designed to reproduce ESP or dipole exactly |
| ADCH | Hirshfeld base plus dipole correction | underlying Hirshfeld result, correction, dipole error, charge closure | reproducing dipole does not make charges unique |
| Hirshfeld-I | density plus iterative charged-atom reference densities | reference-density provenance, iterations, threshold, convergence, final closure | reference generation and iterative convergence are additional failure points |
| CHELPG/MK/RESP | molecular ESP and fitting points | ESP definition, point construction, constraints/restraints, RMSE/RRMSE, conformation and solvent | buried atoms, conformation, grid, and constraints can dominate fitted values |
| MBIS | density and iterative stockholder model | basis/reference convention, integration settings, iteration threshold/history | iterative and model dependent |
| AIM/QTAIM | converged density topology and basin integration | complete CP/basin search, integration residual, ECP/EDF convention | expensive; sensitive to topology/integration completeness |
| EEM/PEOE | structure/connectivity and empirical parameters | parameter set/version, connectivity, iteration details | empirical; not a wavefunction population analysis |

### Common acceptance checks

For every atomic-charge table:

1. verify atom count, symbols, ordering, and coordinate identity against the
   source;
2. require finite values and an explicit charge unit/convention;
3. sum atomic charges and compare with the system net charge; report the raw
   residual rather than silently renormalizing;
4. when spin populations are present, sum them against the expected spin
   convention;
5. preserve all method-specific settings and reference-density provenance;
6. repeat with tighter integration or fitting settings until the intended
   comparison is stable;
7. compare only calculations with compatible method, basis/ECP, geometry,
   solvent, and program settings.

**Practitioner safeguard:** use a tolerance declared before viewing the result.
The appropriate threshold depends on method and use. A charge-sum closure test
detects some errors but cannot validate the physical meaning of the partition.

## Apply method-specific gates

### Mulliken and Lowdin

- Require basis-function identity; `.wfn/.wfx` is insufficient.
- Record restricted/unrestricted spin handling and whether reported values are
  electron populations, spin populations, or net atomic charges.
- Inspect large positive/negative basis contributions and negative populations,
  especially with diffuse or near-linearly-dependent bases.
- For a scientific trend, test at least one reasonable basis variation. If the
  trend or ranking changes materially, report it as basis-sensitive.
- Do not use a smoother-looking Lowdin table as evidence that it is unique or
  experimentally observable.

### Hirshfeld, ADCH, Hirshfeld-I, and MBIS

- Preserve free-atom/charged-atom radial density source, electron/core
  convention, radial/angular integration settings, and any external atomic
  calculation.
- If Multiwfn offers to invoke Gaussian to generate radial densities, stop
  unless that external execution is independently authorized and fully
  versioned. Record atomic configurations and all generated artifacts.
- For Hirshfeld-I and MBIS, retain iteration count, convergence measure, and
  final status. An iteration limit reached is not convergence.
- For ADCH, report both the underlying Hirshfeld charges and the corrected
  charges, the target dipole, reproduced dipole, and residual.
- Check sensitivity to `radpot`, `sphpot`, or the exact equivalent integration
  controls named by the pinned manual when closure is inadequate.

### ESP fitting: CHELPG, MK, and RESP

Record:

- ESP source and electron/nuclear/ECP convention;
- fitting point generation, molecular surface radii/layers, exclusions, and
  grid density;
- total-charge, equivalence, symmetry, dipole, and other constraints;
- RESP stage, restraint functional/strength, equivalence groups, and initial
  values;
- each conformation and its weight for a multi-conformer fit;
- solvent/environment model, method, basis/ECP, and geometry;
- number of points, rank/conditioning warnings, RMSE and relative RMSE, and
  reproduced dipole/ESP diagnostics.

Buried atoms can be poorly determined even when global RMSE is small. Inspect
fit conditioning and sensitivity to reasonable grid/conformation choices.
RESP parameters intended for a force field are model-specific; do not call them
intrinsic atomic charges or transfer them outside the parameterization context
without validation.

## Audit orbital composition

Orbital composition answers a basis- or space-partition question about a
specific orbital. Before main function 8, require:

- basis-function-bearing input and verified atom/basis ordering;
- orbital spin channel, index, occupation, symmetry label if meaningful, and
  energy with an explicit zero/reference;
- producer orbital type: canonical SCF, localized, natural, NBO/NLMO, or other;
- exact composition method such as Mulliken, SCPA, Hirshfeld, or Becke;
- fragment and atom selections resolved against the loaded atom order.

The manual-documented Mulliken stream `8,1,1,2,3` is a tutorial example. The
numbers `1,2,3` identify tutorial orbitals, not a default HOMO/LUMO selection.
Resolve frontier orbitals from occupations and spin, then record the actual
indices supplied to the program.

### Composition closure

For each orbital, retain every atomic/fragment contribution and the sum. A
normalization near the method's expected total is a technical check, not proof
that the partition is chemically privileged. Diagnose failure by checking
spin/index mismatch, basis ordering, ECP semantics, converted Molden dialect,
and numerical integration settings for real-space partitions.

Mulliken/SCPA orbital composition can become unstable with diffuse functions.
When a chemical claim depends on a percentage, compare a real-space partition
or a sensible basis variation and report disagreement rather than selecting the
more convenient number.

### Orbital delocalization index

Treat ODI as a comparative descriptor under one method, basis, orbital type,
and system family. Do not interpret a single absolute ODI as a universal
localization threshold. Preserve whether the orbital was canonical or
localized and the exact composition scheme used to calculate ODI.

## Audit bond-order routes

State the question first: pairwise covalency trend, multicenter delocalization,
fragment interaction, or comparison with a defined reference. Main function 9
contains multiple non-equivalent definitions.

### Mayer bond order

- Require basis-function identity, overlap/density data, and exact spin
  convention.
- Record the Mayer variant used for restricted/open-shell data and any valence
  or free-valence output.
- Check matrix symmetry where expected, diagonal/self terms, and atom ordering.
- Inspect basis-set sensitivity, particularly with diffuse functions and ECPs.
- Compare only values from compatible electronic-structure levels and Mayer
  definitions.

The interactive prefix `9,1` establishes entry to the Mayer route only. Capture
later prompts, selected atoms, matrix-export choice, output filename, and
return token before batching. A generated `bndmat.txt` in an old directory is
not evidence of the current run.

### Fuzzy bond order

- Preserve the atomic-space partition, integration grid, and convergence
  settings.
- Check global or per-atom sum rules documented for the selected output and
  report residuals.
- Refine both spatial integration and source-wavefunction quality.
- Do not compare directly with Mayer values as though they share one scale.

The manual prefix `9,7` is not a complete stdin stream.

### Multicenter bond order and aromaticity descriptors

- Record the ordered atom set, center count, cyclic ordering, spin treatment,
  partition/basis definition, and whether the raw or normalized index is used.
- Raw multicenter indices generally change scale with center count; use a
  documented normalized form for cross-ring comparisons only when its
  assumptions apply.
- Explore plausible atom orderings and reference systems for nonstandard rings.
- If the NAO route depends on NBO output/density matrices, preserve the NBO
  version, source job, orbital convention, and file identity.
- Do not turn one index into a binary aromatic/nonaromatic label. Compare
  several compatible descriptors and structural/electronic evidence.

### Delocalization indices and basin-derived bonds

Require completed topology/basin integration, electron-count closure, and
stable interbasin integrals. Report the partition and integration residual.
Do not compare basin-derived values with basis-space bond orders without
explaining that they are distinct definitions.

## Analyze localized orbitals and fragments

For orbital localization or fragment analyses:

1. identify the input orbital subspace and occupations;
2. record localization method, objective, convergence threshold, iterations,
   initialization, and any frozen/excluded orbitals;
3. retain the transformation matrix or sufficient lineage to reproduce it;
4. verify orthonormality and preservation of the selected subspace;
5. treat rotations within degenerate/nearly degenerate subspaces as potentially
   nonunique;
6. define fragments by explicit atom indices and a saved atom map.

A localized orbital picture is representation-dependent. Avoid language that
implies the localization is the unique electronic structure.

## Produce an auditable table

For a charge, composition, or bond-order result, the handoff should include:

```text
result_id
source_sha256
multiwfn_version_and_executable_sha256
task_and_exact_method
atom_or_orbital_map
method_settings
raw_values_with_units_or_dimensionless_label
closure_or_residual
refinement_or_sensitivity_result
technical_status
scientific_limitations
```

Keep raw tables alongside normalized tables. If the repository's artifact
manifest is used, list both and record their hashes; the manifest validates
identity and structure, not interpretation.

## Common failure patterns

| Symptom | Diagnose | Do not do |
|---|---|---|
| Charges do not sum to net charge | atom mapping, parser columns, integration/fitting convergence, ECP convention | silently distribute the residual without recording it |
| Huge alternating Mulliken values | diffuse basis, linear dependence, wrong basis convention/export | present them as literal electron transfer |
| Hirshfeld-I stops after many cycles | reference densities, iteration threshold, atomic state, integration quality | call the last iteration converged |
| ESP fit RMSE is small but one atom is unstable | buried atom, ill-conditioned design, conformation/grid dependence | infer every fitted charge is well determined |
| Orbital contributions do not close | wrong spin/index, incompatible Molden order, ECP/basis issue, method normalization | renormalize before diagnosing provenance |
| Bond order changes strongly with basis | descriptor sensitivity or source inconsistency | select one basis and claim a unique bond order |
| Multicenter index collapses with ring size | raw index scaling with center count | compare raw values across different center counts |
| Export table belongs to a prior run | fixed filename/stale scratch | accept mtime alone; require pre-run absence and hash/transcript linkage |

Technical acceptance establishes that the intended method consumed the intended
source and produced a closed, traceable table. Scientific acceptance still
requires method suitability, numerical/basis sensitivity, compatible
comparisons, and a claim no stronger than the chosen partition supports.
