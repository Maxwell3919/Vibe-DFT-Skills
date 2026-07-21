# Production acceptance checklists

Use these checklists with the exact commands in `calling-and-recipes.md`. They turn an
officially documented Phonopy route into an auditable calculation handoff and review sequence.
They do not establish native execution in this repository.

## Contents

- [Keep evidence labels explicit](#keep-evidence-labels-explicit)
- [Freeze the exact version and workflow manifest](#freeze-the-exact-version-and-workflow-manifest)
- [Accept displacement setup](#accept-displacement-setup)
- [Converge the supercell and displacement amplitude](#converge-the-supercell-and-displacement-amplitude)
- [Accept each parent force calculation](#accept-each-parent-force-calculation)
- [Collect displacement-force data correctly](#collect-displacement-force-data-correctly)
- [Accept force constants](#accept-force-constants)
- [Accept bands, meshes, DOS, and thermal properties](#accept-bands-meshes-dos-and-thermal-properties)
- [Accept non-analytical correction data](#accept-non-analytical-correction-data)
- [Accept a QHA series](#accept-a-qha-series)
- [Triage failures without weakening science](#triage-failures-without-weakening-science)
- [Apply the current documentation-drift stop](#apply-the-current-documentation-drift-stop)
- [Primary official sources](#primary-official-sources)

## Keep evidence labels explicit

- **Official manual fact** is supported by a first-party Phonopy page or the tag-pinned source.
  It is not evidence that the command ran here.
- **Operational heuristic** is a conservative practice from finite-displacement and
  quasi-harmonic workflows. Validate it for the material, force calculator, and target
  observable; it is neither an official default nor an acceptance threshold.
- **Project threshold** is a numeric acceptance value chosen and justified for the current
  campaign. Never import a threshold from this reference without recording that decision.

Keep software completion, parent-calculation validity, data lineage, numerical convergence,
physical validity, and scientific claim acceptance as separate gates.

## Freeze the exact version and workflow manifest

Before setup, record the following in a machine-readable manifest:

| Area | Required fields |
|---|---|
| Software | Phonopy distribution version, module path/hash, every console-script path/hash, Python, spglib, NumPy, symfc/other fitter, calculator interface, optional dependencies, platform, and environment lock hash. |
| Source structure | Immutable hash, format, ordered species/coordinates, cell, PBC, units, site IDs, charge/spin state, relaxation provenance, and acceptance decision. |
| Phonopy model | Calculator selector, unit cell, supercell matrix, resolved primitive matrix, symmetry tolerance, displacement method/amplitude, plus-minus policy, random seed if any, and generated YAML hash. |
| Force parents | One displacement ID to input/output pair per row, structure hash, atom mapping, calculator version, potential/basis identity, method, convergence settings, job identity, completion, SCF, and force acceptance. |
| Properties | Force-data or force-constant hash, NAC identity, mesh/path/temperature/smearing settings, output hashes, units, and observable-specific convergence comparison. |

For an installed copy, inspect identity with the pinned-compatible calls:

```text
command -v phonopy
command -v phonopy-init
python -c 'import phonopy; print(phonopy.__version__)'
phonopy -h
phonopy-init -h
```

Do not guess `phonopy --version`; the 4.3.1 pinned parser does not register that option. A module
version match is still insufficient if the invoked console script resolves to another
environment.

## Accept displacement setup

Use `phonopy-init` for v4 setup. Run in a new, bounded directory and preserve stdout/stderr:

```text
phonopy-init -d --dim 2 2 2 --pa auto -c UNITCELL
```

Treat `2 2 2` as a tutorial matrix, not a converged choice. After generation, require:

1. `phonopy_disp.yaml` is new, parseable, and bound to the intended source structure hash.
2. The requested supercell matrix and the resolved primitive matrix are printed and stored.
   The v4 default primitive policy is `auto`; never assume the v3 identity matrix.
3. Perfect and displaced supercells have the expected atom count, cell, species order, and PBC.
   For an integer supercell transform `S`, the count and volume scale by `abs(det(S))`.
4. Every generated displacement has a unique ID, displaced atom, Cartesian displacement vector,
   structure hash, and complete unit-cell-to-supercell site/image mapping.
5. The number of generated files agrees with the displacement dataset. No file was overwritten,
   and no stale output from another matrix or amplitude remains in the collection directory.
6. Symmetry reduction is plausible for the declared tolerance. An unexpectedly small or large
   displacement count triggers a symmetry and structure review, not an automatic continuation.

Shell glob order is not evidence. Build the force-file argument list from displacement IDs and
verify every pair before collection.

## Converge the supercell and displacement amplitude

There is no universal converged matrix or displacement amplitude. Converge both against the
observable that will support the claim.

### Supercell convergence

For each candidate matrix, hold the primitive-cell definition, force method, displacement
policy, and property settings fixed. Compare at least:

- selected frequencies at symmetry and suspected soft-mode q points;
- eigenvector overlap or mode tracking when branches reorder;
- acoustic behavior near Gamma and force-constant drift;
- target DOS, free energy, heat capacity, or other reported observable;
- runtime and atom-count cost only after the scientific differences are known.

**Operational heuristic:** start with a matrix that makes the shortest periodic image separation
reasonably isotropic for the crystal, then extend the shortest real-space direction first. This is
usually more informative than increasing all diagonal repeats blindly. Low-dimensional systems
need in-plane force-range convergence; vacuum thickness is a separate electronic-structure and
electrostatic decision, not a phonon-supercell repeat.

Accept the smaller matrix only when differences to a larger, independently accepted matrix are
below a documented project threshold for every claimed observable. A visually similar band plot
is not a convergence test.

### Displacement-amplitude convergence

Record an explicit Cartesian amplitude even when relying on a documented default. Compare at
least two amplitudes with identical parent-calculation settings.

**Operational heuristic:** `0.005`, `0.01`, and `0.02` angstrom form a useful diagnostic bracket
for many well-behaved DFT force calculations. They are not universal recommendations. Increase
the amplitude only after showing that force noise dominates; decrease it only after showing that
anharmonic contamination dominates.

Where plus/minus pairs exist, compare the odd force response and the residual even component.
Large nonlinearity, inconsistent mode shifts, or amplitude-dependent imaginary branches block a
harmonic claim. Tighten the parent force calculation or reconsider the harmonic model before
selecting the most favorable amplitude.

## Accept each parent force calculation

One parser-readable force file per displacement is necessary but not sufficient. Route VASP,
QE, or another parent through its rigorous-calculation Skill and require:

1. The exact generated displaced structure was used without atom reordering or ionic relaxation.
2. Calculator, potential/basis, relativistic treatment, charge/spin, cell, k-point density,
   cutoffs, smearing/occupations, electronic convergence, and precision settings are consistent
   across all displacement and perfect-supercell runs.
3. The calculation completed normally, its final electronic step converged, and one finite
   Cartesian force vector exists for every atom in the expected unit and order.
4. No geometry step changed the displacement. For VASP, the official example uses a static force
   calculation (`IBRION=-1`) with tight electronic settings; target-specific sufficiency remains
   owned by `vasp-rigorous-calculations`. For QE, explicitly request and validate printed forces;
   target-specific settings remain owned by `qe-rigorous-calculations`.
5. Total-force drift, per-atom force magnitude, SCF residual, warnings, and output identity are
   retained. Parser success never erases a parent warning or unconverged SCF step.

**Operational heuristic:** pre-converge the perfect supercell using the same numerical settings
before launching all displacements. A small pilot containing one symmetry-inequivalent plus/minus
pair can expose atom-order, unit, force-noise, and filesystem problems before the full campaign.

Do not reuse an accepted force from a different cell, atom order, primitive matrix, displacement
amplitude, potential/basis set, spin state, or numerical setup merely because the filename fits.

## Collect displacement-force data correctly

### Type-1 systematic finite displacements

**Official manual fact:** type-1 `FORCE_SETS` starts with the supercell atom count and number of
displaced supercells. Each block records one displaced atom, its Cartesian displacement, and all
supercell forces. Phonopy's built-in finite-difference force-constant calculator can use it.

Collect an explicit ordered list:

```text
phonopy-init --vasp --sp -f disp-001/vasprun.xml disp-002/vasprun.xml ...
phonopy-init --qe --sp -f disp-001/pw.out disp-002/pw.out ...
```

`--sp` stores the displacement-force dataset in `phonopy_params.yaml` instead of a standalone
`FORCE_SETS`; compatible BORN data found during save can also be embedded. Hash and inspect the
result rather than assuming self-contained means correct.

### Type-2 displacement-force arrays

**Official manual fact:** every type-2 row has six numbers: three Cartesian displacement
components followed by three force components. Consecutive groups of `num_atoms` rows form
supercell snapshots, giving arrays shaped `(num_supercells, num_atoms, 3)`. Fitting requires an
external force-constant calculator such as symfc or ALM.

```text
phonopy phonopy_params.yaml --fc-calculator symfc --writefc
```

Record dataset type, snapshot count/order, units, fitter and version, options, regularization or
cutoff, full versus compact output, and train/validation diagnostics. Do not feed type-2 random
data to a built-in systematic finite-difference assumption.

For an unsupported calculator, current official documentation specifies displacements in
angstrom and forces in eV/angstrom to obtain the normal Phonopy THz convention. A custom adapter
must prove its conversion and atom mapping; a six-column text shape alone is not evidence.

### Residual-force subtraction

**Official manual fact:** `phonopy-init --fz PERFECT_RESULT DISPLACED_RESULTS...` places the
perfect-supercell result first and subtracts those residual forces. The perfect supercell must
have the same atom count, order, cell, and calculator settings. The official docs expect this to
be most useful when plus-minus displacements are disabled; accurate plus-minus pairs should
cancel residual forces. Non-VASP interfaces are explicitly described as not tested on the page.

Do not apply `--fz` reflexively to hide force drift. First determine whether drift comes from an
unrelaxed reference, inconsistent settings, insufficient SCF convergence, atom mapping, or a
genuine symmetry-breaking state. Preserve both raw and corrected datasets and the perfect-run
identity.

### Collection acceptance

Require all of the following after collection:

- one accepted result for every expected displacement, with no duplicate or extra ID;
- displacements reconstructed from generated versus calculated structures agree within a
  declared tolerance;
- atom order, cell, species, units, and force-array shapes match throughout;
- the collected YAML or FORCE_SETS contains finite values and the expected dataset type;
- parser stdout names the intended interface and inputs, and no warning was ignored;
- raw parent outputs, collection command, ordered argument manifest, and collected hash remain
  linked.

## Accept force constants

**Official manual fact:** force constants may be full
`(n_satom, n_satom, 3, 3)` or compact `(n_patom, n_satom, 3, 3)`. A compact HDF5 file requires
the primitive-to-supercell map (`p2s_map`). Direct `phonopy-init --fc vasprun.xml` import is
VASP-only in the pinned recipe.

Check:

1. Array shape, finite values, index convention, units/interface factor, and `p2s_map` agree with
   the exact primitive and supercell models.
2. Translation, permutation, and point-group symmetry residuals are recorded before and after any
   symmetrization. Never report only the repaired value.
3. Gamma acoustic modes, questionable eigenvectors, and any imaginary branches are inspected.
   There is no universal acceptable drift or near-zero-frequency cutoff.
4. Force constants are stable against the chosen supercell, displacement amplitude, force
   settings, symmetry treatment, and fitter configuration.
5. For fitted random/type-2 data, held-out force errors and configuration coverage are acceptable
   for the target property. A low global RMSE can still miss a soft mode or rare distortion.

**Operational heuristic:** compare force constants by their reproduced forces and resulting
observables, not only element-wise norms; symmetry-equivalent representations and branch
reordering can make naive array differences misleading.

Acoustic sum-rule enforcement or symmetrization can be a documented numerical treatment, but it
cannot substitute for identifying large raw violations.

## Accept bands, meshes, DOS, and thermal properties

### Bands and selected q points

- Record paths in reduced reciprocal coordinates of the resolved primitive cell, labels,
  segment boundaries, points per segment, NAC state, and frequency units.
- Retain signed frequencies. Track eigenvectors or overlaps when comparing convergence or modes
  across changing cells; sorting frequencies by value is insufficient near crossings.
- For `--band auto`, record the Seekpath version and exact returned path. Do not compare it to a
  different primitive setting as if labels were invariant.
- Inspect suspicious modes with eigenvectors and, when needed, frozen-mode distortions. A single
  small negative frequency is neither automatic instability nor automatic numerical noise.

### Mesh, DOS, and PDOS

- Record the actual mesh emitted by Phonopy, shifts, symmetry reduction, frequency range,
  broadening/tetrahedron choice, normalization, and primitive-cell definition.
- Converge the requested integral or curve feature with successively denser actual meshes.
- Check total-DOS mode count under the documented normalization and compare summed PDOS with the
  total DOS. PDOS atom indices follow primitive-cell order; preserve the index-to-site map.
- A smooth curve obtained by large broadening is not mesh convergence.

### Thermal properties

- Record mesh, `TMIN`, `TMAX`, `TSTEP`, unit block, primitive-cell normalization,
  `num_modes`, and `num_integrated_modes` from `thermal_properties.yaml`.
- Converge free energy, entropy, and heat capacity against the actual mesh and relevant frequency
  cutoff policy.
- **Official manual fact:** `PRETEND_REAL` produces false thermal properties and is for testing
  only. Never use it to support stability or thermodynamic claims.
- Any excluded imaginary or low-frequency modes must be counted, justified, and propagated as a
  limitation. A successful thermal-properties file does not make an unstable harmonic model
  thermodynamically valid.

## Accept non-analytical correction data

In pinned v4 behavior, NAC is automatic when compatible `BORN` or embedded `nac_params` exists;
`--nonac` disables it. Do not add the removed main `--nac` flag even though an unversioned input
page retains old wording.

Generate calculator-specific data only from an independently accepted response calculation:

```text
phonopy-vasp-born vasprun.xml > BORN
phonopy-qe-born UNITCELL.in RESPONSE.out > BORN
```

Verify:

1. Source structure, primitive matrix, atom order, calculator method, potential/basis, charge/spin,
   and units match the phonon model.
2. The dielectric tensor is finite and physically plausible; every required independent
   primitive atom has a 3x3 Born effective-charge tensor.
3. The BORN conversion factor/interface is correct. The file order is factor, nine dielectric
   components, then Born tensors for the independent primitive atoms.
4. Symmetry-related tensors agree within the response-calculation accuracy and the Born-charge
   acoustic sum is inspected before any correction.
5. Verbose Phonopy output states that NAC parameters were read and used. Preserve this log.
6. The non-analytic behavior is checked along relevant directions approaching Gamma and compared
   with a deliberately `--nonac` calculation to prove activation and understand its effect.

**Operational heuristic:** an unexpectedly large charge-sum violation or dielectric asymmetry is
usually a reason to revisit the response calculation, mapping, or numerical convergence before
symmetrizing the tensors.

NAC affects the long-range non-analytic term. It does not repair short-range force constants,
imaginary modes away from Gamma, or an unconverged parent calculation.

## Accept a QHA series

### Build the volume manifest first

Create one immutable row per volume containing:

- ordered index, structure hash, cell shape, static cell volume, primitive volume and
  normalization multiplier;
- relaxation constraint and acceptance, static-energy value/unit/hash, calculator settings;
- phonon YAML and force-data hash, supercell and primitive matrices, NAC policy, q mesh,
  temperature grid, imaginary-mode policy, and phonon acceptance;
- exact thermal-properties filename passed to `phonopy-qha`.

**Official manual fact:** `phonopy-qha` needs at least five volume points. `e-v.dat` uses cell
volume in angstrom cubed and non-phonon energy in eV. Thermal-property files must follow exactly
the same order as the volumes and use the same temperature range and step. Numerical
differentiation yields one temperature point fewer, so calculate at least one point above the
requested QHA maximum.

### Prepare a defensible volume series

Hold composition, electronic method, potential/basis, charge/spin, k-point density, cutoffs,
energy normalization, and convergence criteria consistent. Use the same phonon acceptance
policy at every volume. Record how internal coordinates and cell shape were relaxed at fixed
volume or under hydrostatic pressure.

**Operational heuristic:** seven to eleven volumes, often spaced by roughly one or two percent
around the static minimum, provide a more diagnostic fit than the five-point minimum. This is not
a universal range: expand or tighten it based on curvature, phase changes, magnetism, and the
temperature-dependent equilibrium trajectory.

The sampled range must bracket the static and all reported temperature-dependent equilibrium
volumes. If the optimum approaches an endpoint, extend the series rather than extrapolating a
claim.

### Run and accept the fit

```text
phonopy-qha e-v.dat thermal-properties-in-volume-order...
phonopy-qha --eos birch_murnaghan -b e-v.dat
```

Require:

1. Every input phonon model passed its independent supercell, force, mesh, and imaginary-mode
   gates; a QHA fit cannot average away a failed volume point.
2. Static energy versus volume is smooth at the required precision and the minimum is bracketed.
3. Vinet, Birch-Murnaghan, and Murnaghan sensitivity is inspected where it affects the claim;
   fit residuals, equilibrium volume, bulk modulus, and outlier influence are retained.
4. Equilibrium volume versus temperature is smooth, remains inside the sampled range, and is
   compatible with the supplied shape-versus-volume path.
5. Gibbs energy, thermal expansion, bulk modulus, and heat-capacity outputs are parseable, finite,
   correctly normalized, and stable to volume-grid and q-mesh changes.
6. Imaginary modes and any excluded volume/temperature interval are explicit. Do not use
   `PRETEND_REAL` to make a QHA series fit.

**Official manual fact:** bulk modulus from nonzero `--pressure` is documented as incorrect. QHA
minimizes free energy along the supplied volume/shape path; it is not a full anisotropic
`F(a,b,c;T)` minimization. Label `--efe` experimental and do not mix its electronic-contribution
semantics with phonon-only heat-capacity products.

## Triage failures without weakening science

| Symptom | Likely causes | Required response |
|---|---|---|
| Wrong number of force files | stale files, failed parent, shell ordering, changed symmetry setup | Rebuild an explicit displacement-ID manifest; do not collect a partial accidental set. |
| Force parser succeeds but acoustic modes drift | unconverged forces, residual force, mapping, inconsistent settings, inadequate supercell | Inspect raw forces and parent evidence; use `--fz` only with a matched perfect run and documented rationale. |
| Imaginary branch moves strongly with amplitude | force noise or anharmonicity | Tighten parent forces and run an amplitude ladder; do not choose the amplitude that removes it. |
| Imaginary branch moves strongly with supercell | truncated real-space force constants | Extend the limiting direction and track the eigenvector/q point. |
| NAC produces no visible/logged change | BORN not read, wrong directory/YAML, primitive mismatch, or nonpolar mode/path | Prove activation in verbose output and compare with `--nonac`. |
| PDOS does not sum to total DOS | wrong primitive indices, projection grouping, mesh/broadening mismatch | Rebuild the site map and rerun identical mesh settings. |
| QHA equilibrium lies at volume endpoint | range does not bracket the minimum or inconsistent normalization | Extend/recompute the volume series; do not extrapolate silently. |
| QHA curve is jagged | inconsistent static settings, unconverged phonons, mode discontinuity, wrong file order | Audit the volume manifest and each parent; do not smooth away the evidence. |
| Only post-symmetrization drift is small | raw force constants violate invariances | Report both values and diagnose the raw violation before acceptance. |

## Apply the current documentation-drift stop

The recipe/catalog authority in this Skill is exact Phonopy `4.3.1`. On 2026-07-22 the
unversioned official site rendered some pages as `4.4.0`, including input-files, setting-tags,
and QHA content, while the migration and command pages could still show 4.3.1 content. Do not
silently import 4.4.0 commands, defaults, Python APIs, or output semantics into this profile.

Block 4.4.0 as `PHONOPY_VERSION_UNSUPPORTED` until a reviewed update provides a tag/source pin,
parser and entrypoint catalog, migration review, fixtures, exact native help, output audits, and
cross-skill parent handoff tests. When same-site pages conflict, retain the Skill's existing
source-first precedence order.

## Primary official sources

- v4 migration and command split:
  <https://phonopy.github.io/phonopy/migration-v4.html>,
  <https://phonopy.github.io/phonopy/phonopy-init.html>, and
  <https://phonopy.github.io/phonopy/phonopy.html>.
- Inputs, settings, outputs, and command options:
  <https://phonopy.github.io/phonopy/input-files.html>,
  <https://phonopy.github.io/phonopy/setting-tags.html>,
  <https://phonopy.github.io/phonopy/output-files.html>, and
  <https://phonopy.github.io/phonopy/command-options.html>.
- Calculator interfaces:
  <https://phonopy.github.io/phonopy/vasp.html>,
  <https://phonopy.github.io/phonopy/qe.html>, and
  <https://phonopy.github.io/phonopy/vasp-dfpt.html>.
- NAC, random displacements, QHA, and Gruneisen:
  <https://phonopy.github.io/phonopy/formulation.html#non-analytical-term-correction>,
  <https://phonopy.github.io/phonopy/random-displacements.html>,
  <https://phonopy.github.io/phonopy/qha.html>, and
  <https://phonopy.github.io/phonopy/gruneisen.html>.
- Tag/release source and changelog:
  <https://github.com/phonopy/phonopy> and
  <https://phonopy.github.io/phonopy/changelog.html>.
