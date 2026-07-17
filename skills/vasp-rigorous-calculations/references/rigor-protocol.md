# Rigorous VASP evidence protocol

Use this protocol to design or review a production calculation. It is a scientific-validation workflow, not an official VASP prescription. Cite official Wiki pages separately for software behavior.

## Contents

1. Claim-first design
2. Reproducibility record
3. Numerical convergence
4. Structural and electronic integrity
5. Model validation
6. Comparability
7. Reporting matrix

## 1. Claim-first design

Write the intended claim before choosing parameters:

- target system and state;
- target observable, including normalization and reference state;
- acceptable absolute or relative uncertainty;
- required ranking stability or qualitative invariance;
- environmental and model assumptions.

Examples of distinct observables include energy differences per atom, adsorption energy, maximum force, stress component, band gap, band ordering, magnetic moment, phonon frequency, migration barrier, dielectric response, and spectral peak position. A setting converged for total energy may not be converged for forces, stress, unoccupied bands, response functions, or small energy differences.

## 2. Reproducibility record

Preserve the following for every production stage:

- VASP version, build date if printed, executable identity, parallel layout, and relevant environment;
- all input files and the exact command or scheduler script;
- parent calculation identity for restarts or fixed-density calculations;
- POTCAR dataset order, family/release metadata available locally, `TITEL`, `LEXCH`, `ENMAX`, and a local SHA-256; never redistribute POTCAR contents;
- structure provenance, transformations, constraints, charge, stoichiometry, and atom ordering;
- exact exchange-correlation, dispersion, Hubbard, hybrid, SOC, dipole, external-field, and finite-size choices;
- convergence-series data and acceptance criteria;
- final output, warnings, completion evidence, and parser versions.

Hashing proves file identity, not scientific suitability.

## 3. Numerical convergence

### General design

1. Choose a representative but affordable system and workflow stage.
2. Define the observable and tolerance before seeing the preferred result.
3. Change one control at a time unless testing an interaction.
4. Use a consistent calculation path and restart policy.
5. Include at least three points in the apparent stable region when feasible.
6. Inspect the whole series for oscillation, discontinuity, symmetry changes, magnetic transitions, or failed electronic convergence.
7. Retest coupled controls when one changes the conclusion of another.
8. Select a production point with a stated margin, not merely the cheapest passing point.

### Plane-wave basis and grids

Test `ENCUT` against the actual observable. Keep POTCAR datasets fixed. For stress, cell relaxation, energy-volume curves, hard species, response properties, and small energy differences, examine basis sensitivity explicitly. Inspect the official pages for `ENCUT`, `PREC`, FFT-grid controls, and any method-specific augmentation settings before interpreting behavior.

Do not infer convergence from `ENMAX` alone. `ENMAX` is POTCAR metadata and a software default input to basis selection; adequacy remains observable-specific.

### Brillouin-zone sampling

Keep the mesh family, centering rule, and symmetry treatment controlled while increasing density. Compare like-for-like meshes when possible. Metallic Fermi surfaces, low-dimensional cells, distorted cells, magnetic order, and response calculations may require separate sampling studies.

Report the actual mesh or irreducible-point count and the construction rule. A k-point density label without the resulting mesh is incomplete.

### Occupations and smearing

Treat smearing method and width as numerical/model controls. Check the relevant energy quantity and extrapolation convention stated by the official documentation. For metals, test the stability of energies, forces, moments, and density of states. For insulators or final static calculations, verify that the selected method is compatible with the intended observable and sampling.

### Electronic minimization

Test that the electronic stopping criterion is tighter than the uncertainty budget of the derived observable. Confirm every ionic or response step reaches the intended electronic behavior. Review algorithm-specific prerequisites and warnings in the official documentation and actual output.

### Ionic and cell optimization

Define convergence in forces and, for variable-cell work, stress and lattice quantities. Verify that the final configuration is not only stopped by a step limit. Recompute a clean static calculation on the final structure when the target property requires it. Check basis-set and k-point effects on stress before trusting cell parameters.

### Finite representations

Test the controls created by the physical model:

- vacuum and slab thickness for surfaces and 2D systems;
- lateral size and defect-image separation for defects, adsorbates, polarons, and magnetic textures;
- charge-correction and potential-alignment conventions for charged cells;
- displacement size and supercell for finite-displacement phonons;
- image number, spring/path settings, and endpoint quality for NEB;
- empty bands, frequency grids, and response cutoffs for excited-state methods;
- q meshes, interpolation, and broadening for electron-phonon or response workflows.

## 4. Structural and electronic integrity

Before accepting results, inspect:

- POSCAR species and POTCAR dataset order;
- unintended symmetry changes or symmetry suppression;
- atoms at cell boundaries, duplicate atoms, unrealistic distances, and constraint flags;
- charge/spin state and electron count;
- magnetic initialization and final local/total moments;
- whether the final electronic state is the intended metastable or ground-state candidate;
- maximum force, stress tensor, ionic step count, and cell change;
- all warnings and the last complete electronic/ionic step;
- whether post-processing uses the intended structure, charge density, wavefunctions, k path, and number of bands.

A clean termination line does not demonstrate correct physics.

## 5. Model validation

Numerical convergence holds a model fixed. Test model choices when they can change the claim:

- exchange-correlation functional;
- dispersion correction for layered, molecular, adsorption, or interface systems;
- Hubbard parameters and projector choices;
- SOC for heavy elements, anisotropy, band topology, or small splittings;
- collinear versus noncollinear magnetism and competing magnetic orders;
- pseudopotential valence configuration or hardness;
- slab electrostatics, dipole corrections, and charged-boundary treatment;
- finite temperature, zero-point effects, anharmonicity, or disorder where relevant.

Distinguish a sensitivity study from a convergence study.

## 6. Comparability

For relative energies or trends, verify that compared cases share all choices that should cancel:

- compatible POTCAR files in consistent species order;
- identical method and correction definitions;
- equivalent basis policy and sampling accuracy;
- equivalent spin, SOC, symmetry, charge, and finite-size conventions;
- equivalent relaxation/static workflow and reference energies;
- consistent normalization and sign conventions.

If atom counts or compositions differ, define the thermodynamic reference and chemical potentials explicitly.

## 7. Reporting matrix

For each decisive control, report:

| Control | Values tested | Observable | Acceptance criterion | Stable tail | Production choice | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `ENCUT` | actual values | named quantity | stated tolerance | actual changes | chosen value | demonstrated / unresolved |
| k sampling | actual meshes | named quantity | stated tolerance | actual changes | chosen mesh | demonstrated / unresolved |
| model size | actual sizes | named quantity | stated tolerance | actual changes | chosen size | demonstrated / unresolved |

Also report official citations for tag behavior, output evidence for actual settings, and open limitations. Never replace the tested values with vague phrases such as “dense mesh” or “high cutoff.”
