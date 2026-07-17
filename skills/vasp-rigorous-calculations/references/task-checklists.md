# VASP task checklists

Use only the sections relevant to the task. These are audit prompts, not universal parameter recipes. Resolve tag behavior against the matching official VASP Wiki pages.

## Contents

1. Relaxation and equation of state
2. Static energies and energy differences
3. Bands and density of states
4. Magnetism, SOC, and DFT+U
5. Surfaces, 2D materials, and adsorption
6. Defects and charged cells
7. Phonons and molecular dynamics
8. NEB and barriers
9. Hybrid, GW, optics, and response

## 1. Relaxation and equation of state

- Identify fixed and relaxed degrees of freedom.
- Verify `IBRION`, `NSW`, `ISIF`, `EDIFF`, and `EDIFFG` semantics from official pages.
- Confirm the run stopped for the intended convergence condition rather than step or wall-time exhaustion.
- Check final maximum force and relevant stress components directly.
- Test basis and k-point sensitivity of forces/stress; watch Pulay stress in variable-cell work.
- Preserve symmetry and selective-dynamics intent.
- For energy-volume work, use consistent basis, sampling, POTCAR, and electronic settings across volumes and inspect smoothness.
- Run a final static calculation on the accepted structure when required by the downstream observable.

## 2. Static energies and energy differences

- Define reference states, normalization, and sign convention.
- Keep POTCAR datasets, method, basis policy, sampling quality, occupations, spin/SOC state, and corrections comparable.
- Tighten electronic accuracy relative to the target energy difference.
- Verify the actual final energy quantity appropriate to the occupation method.
- Check that all compared states reached the intended electronic and magnetic solution.
- Test finite-size controls and structural-relaxation consistency.

## 3. Bands and density of states

- Use a converged parent density with matching structure, POTCAR, method, spin, SOC, and correction choices.
- Separate self-consistent sampling from line-mode band paths.
- Record the k-path convention and reciprocal coordinates.
- Ensure enough bands for the plotted energy range.
- For DOS/PDOS, converge the sampling and broadening/tetrahedron choice for the feature of interest.
- Verify energy zero, Fermi-level convention, spin channels, and projection definitions.
- Treat apparent crossings, gaps, and orbital characters as unresolved if sampling, SOC, magnetism, or projection leakage can change them.

## 4. Magnetism, SOC, and DFT+U

- Enumerate physically plausible magnetic initial states instead of trusting one `MAGMOM` seed.
- Verify final total and local moments and compare converged metastable states.
- Check cell size and symmetry compatibility with the proposed order.
- For SOC/noncollinear work, document spin-axis convention and orientation-dependent settings.
- Confirm all energy comparisons use the same SOC and magnetic definitions.
- For DFT+U, record formulation, species/orbital mapping, U/J values, projectors, and double-counting convention as defined by the official tags.
- Treat U/J selection as a model choice requiring provenance or sensitivity analysis, not numerical convergence.

## 5. Surfaces, 2D materials, and adsorption

- Converge vacuum, slab thickness, lateral cell, k sampling, and relaxation depth.
- Document symmetric versus asymmetric slab construction.
- Check dipole and electrostatic treatment against the official method requirements.
- Verify adsorption references use compatible cells, methods, POTCARs, and finite-size conventions.
- Test dispersion correction when interactions may be nonlocal.
- Inspect both sides of periodic boundaries and all relevant adsorption/magnetic configurations.
- For work functions, verify the vacuum plateau and potential reference.

## 6. Defects and charged cells

- Define defect stoichiometry, charge state, electron count, and chemical-potential references.
- Converge supercell size and k sampling.
- Document potential alignment and finite-size correction method, assumptions, and dielectric inputs.
- Check spin states, symmetry breaking, localization, and competing geometries.
- Verify band-edge references and functional dependence.
- Keep bulk and defect reference calculations strictly comparable.
- Do not infer a dilute-limit formation energy from one supercell.

## 7. Phonons and molecular dynamics

- For finite displacement, converge supercell and displacement amplitude and verify force accuracy.
- Preserve or intentionally reduce symmetry and document the choice.
- Check acoustic behavior and numerical imaginary modes against tighter settings and larger cells.
- For polar materials, document nonanalytic corrections and required dielectric/Born-charge data when used.
- For MD, document ensemble, thermostat/barostat, time step, equilibration, sampling length, energy drift, and independent replicas when needed.
- Distinguish dynamical instability, numerical noise, anharmonic stabilization, and insufficient sampling.

## 8. NEB and barriers

- Fully converge endpoints with the same method and cell.
- Verify atom mapping and a physically meaningful initial path.
- Test image number and path controls when the saddle region is underresolved.
- Inspect force convergence for every image, not only total run completion.
- Confirm the highest image is a saddle candidate and, when decisive, validate it by an appropriate mode analysis.
- Report forward and reverse reference energies consistently.

## 9. Hybrid, GW, optics, and response

- Read the official workflow page and all method-specific prerequisites before constructing restarts.
- Converge occupied and unoccupied band counts for the target spectrum or quasiparticle range.
- Converge response cutoffs, frequency/time grids, k sampling, and broadening.
- Preserve the exact parent wavefunction/density lineage.
- Record whether eigenvalues, wavefunctions, self-consistency, or screening are updated at each stage.
- Treat a visually smooth spectrum as insufficient without parameter convergence and sum-rule or internal-consistency checks where applicable.
