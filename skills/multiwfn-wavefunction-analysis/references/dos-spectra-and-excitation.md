# DOS, spectra, and electronic-excitation analysis

This reference summarizes the pinned Multiwfn manual's main functions 10, 11,
and 18. It separates raw producer observables, Multiwfn's analytical
representation, and the scientific claim.

## Contents

1. Molecular TDOS, PDOS, and OPDOS
2. Vibrational, electronic, and NMR spectra
3. Electronic-excitation source matching
4. Coefficient and grid closure
5. Peak/state assignment records
6. Troubleshooting

## Molecular DOS is a broadened level representation

For a finite molecule, the underlying orbital energies are discrete. Multiwfn
constructs a continuous-looking TDOS/PDOS/OPDOS curve by applying a broadening
kernel. That graph is not a periodic solid-state DOS merely because the axes
look similar.

Record for every curve:

- producer, method, basis/ECP, geometry, charge/multiplicity, and source hash;
- orbital type, spin channel, occupations, and included orbital range;
- energy unit and zero/reference, including any manually applied shift;
- broadening function, FWHM, plotting/integration range, and sampling step;
- fragment/atom definitions and atom-order map;
- composition method for PDOS and overlap-population definition for OPDOS;
- raw orbital energies/weights plus the generated numerical curve;
- program/banner/settings and command-stream identities.

Changing FWHM changes peak shapes, apparent overlap, and peak maxima. It does
not change the raw orbital energies. Report broadening as an analysis parameter,
not an instrument-independent observable.

### TDOS

TDOS requires orbital energies and occupations. Check the number of levels,
spin convention, energy ordering, and agreement of representative energies
with the producer output. For open-shell systems, preserve alpha and beta
channels rather than silently merging them.

The manual's tutorial energy window is system-specific. Choose a range from
the scientific question and loaded levels; do not copy it as a default.

### PDOS and OPDOS

PDOS/OPDOS requires basis-function identity and a verified atom/basis mapping.
`.wfn/.wfx` alone is ineligible. Define fragments by explicit atom indices and
save the map.

Mulliken/SCPA projections can become unreliable with diffuse functions.
Real-space Hirshfeld/Becke alternatives may be more robust for some PDOS tasks
but cost more and do not supply the same OPDOS definition. Do not splice an
OPDOS curve from one partition into a PDOS interpretation from another without
stating the mismatch.

Check the projected-weight sum against the expected total under the chosen
composition method. Diagnose large residuals; do not automatically normalize
them away.

### Interpretation limits

- An isolated molecule has no uniquely defined Fermi level in the solid-state
  sense. Label HOMO/LUMO or a chosen energy zero precisely.
- A band/energy center depends on the integration window and weights. Report
  both.
- The absolute height of a broadened curve depends on normalization, sampling,
  and FWHM; it is not independently meaningful.
- PDOS overlap suggests energetic/orbital mixing under a partition. It does not
  alone prove charge transfer, bond strength, conductivity, or catalytic
  activity.
- Compare curves only after matching method, energy reference, kernel/FWHM,
  spin treatment, and fragment definition.

## Spectrum input is task-specific producer output

Main function 11 parses supported output or exact special transition text. A
wavefunction file such as `.fch`, Molden, `.wfn`, or `.wfx` is not by itself a
vibrational, UV/Vis, ECD, Raman, or NMR transition list.

Before processing a spectrum, preserve:

- producer code and exact version, complete converged output, and input lineage;
- spectrum type and producer method (harmonic/anharmonic, TDDFT/TDA, response
  model, gauge/representation, solvent, temperature as applicable);
- parser route supported by the pinned Multiwfn version;
- number of parsed transitions/modes and a spot comparison with the source;
- raw frequency/energy and strength units;
- broadening kernel/FWHM, scale factor, shift, temperature, incident-light
  frequency, weighting, and plotting range;
- numerical export and figure as separate artifacts.

The manual's plain transition-text formats use task-dependent units, including
`cm^-1` for vibrational frequencies and `eV` for electronic transitions; the
strength column also changes meaning by spectrum type. Never reuse a two-column
file without preserving its schema and units.

### IR and Raman

- Distinguish harmonic frequencies, IR intensities, Raman activities, and
  Raman intensities. Raman activity is not the experimentally displayed
  intensity without incident-frequency and temperature factors.
- Record any frequency scaling factor and whether it is applied before or
  after broadening.
- Handle imaginary frequencies explicitly; do not silently plot their absolute
  values as normal peaks.
- Preserve mode order and compare selected source frequencies/intensities
  against the parsed list.
- **Version fact:** the official update history records a CP2K Raman parsing fix
  on `2026.3.18`. Pin the program update date for any CP2K Raman result and
  revalidate older curves if they may have used an affected build.

### UV/Vis and ECD

- Preserve excitation energies/wavelengths, oscillator strengths or rotatory
  strengths, state indices, spin/symmetry labels, and the exact response
  method.
- For ECD, record length versus velocity representation. The manual notes the
  length representation's origin dependence and the velocity representation's
  different origin behavior; basis convergence still matters.
- A broadened peak can contain multiple transitions. Keep a transition-to-peak
  assignment table rather than assigning only from the plotted maximum.
- Do not infer charge-transfer character from a spectrum alone; use a matching
  excitation-analysis route and orbital/real-space evidence.

### NMR

- Distinguish absolute shielding from chemical shift.
- Convert shielding to shift only with a reference computed under a compatible
  method, basis/ECP, solvent, geometry, and relativistic treatment, or with a
  documented calibration/scaling model.
- Preserve nucleus/isotope mapping, conformer-specific values, conformer
  energies, temperature, weighting model, and reference identity.
- A visually close spectrum does not establish assignments when peaks overlap;
  retain the atom-to-line mapping and uncertainties.

### Mixtures and weighted spectra

For conformers, species, or states, retain every component spectrum before
mixing. Record weights, their physical source, normalization, temperature, free
energy model, degeneracy, and any empirical adjustment. Do not optimize weights
to match experiment without labelling the fit and reporting sensitivity.

## Electronic-excitation analysis needs two matching sources

The pinned manual formally targets single-reference TDDFT/TDA/CIS/TDHF-style
configuration analyses under its documented producer routes. Do not assume
that a parser accepting text establishes theoretical validity for arbitrary
multireference or post-HF excitation methods.

### Intake gate

Require both:

1. a basis/MO source with geometry, orbitals, occupations, spin, and basis; and
2. a supported output or converted file containing excitation coefficients.

Match atom order and coordinates numerically, method/basis/ECP, charge and
multiplicity, solvent, restricted/unrestricted convention, MO counts, job or
restart lineage, and state ordering. Refuse a pair assembled by similar
basename or excitation energy alone.

### Producer-specific coefficient risks

- Gaussian output can omit coefficients below a print threshold. Record the
  configured threshold and verify coefficient completeness.
- ORCA CIS/TDA routes require the documented print controls. ORCA TDDFT may
  require a JSON export through `orca_2json`; version and hash that converter.
- ORCA sTDA/sTDDFT output may print only the largest few configurations, making
  the displayed list unsuitable for normalized hole/electron analysis.
- CP2K, BDF, and other routes have version- and method-specific parser
  boundaries. Follow only the pinned manual's exact supported case.

Every converter is a separately authorized adapter. Capture command, version,
stdout/stderr, input/output hashes, and a structural comparison with the
original output.

### Normalize according to the producer convention

Record whether a coefficient is an amplitude, a spin-adapted coefficient, or
another quantity, and the normalization expected by the manual for that
producer/method. For example, a closed-shell Gaussian-style convention can
have a sum of squared printed coefficients near `0.5` rather than `1`.
Do not force all sources to a single assumed normalization.

Before plotting a state, report:

- sum of included squared coefficients under the exact convention;
- omitted/truncated weight if it can be determined;
- dominant configurations with spin and occupied/virtual indices;
- excitation energy and state identifier cross-checked to the producer output.

If the coefficient set is incomplete or normalization is inconsistent, mark
hole/electron and transition-density results blocked.

## Validate hole, electron, and transition-density grids

For the documented main-function-18 workflow, record state, spin, grid box,
spacing, coefficient threshold/completeness, output filenames, and all menu
responses. Use a fresh directory because `hole.cub` and `electron.cub` can be
fixed-name outputs.

Under the manual's ideal normalized definitions:

- whole-space hole integral should approach `1`;
- whole-space electron integral should approach `1`;
- whole-space transition-density integral should approach `0`.

Treat these as numerical closure checks under the selected convention. If they
fail, test coefficient completeness, source matching, box extent, spacing,
spin/state selection, and output field identity. Do not renormalize a visibly
truncated grid and call it validated.

Preserve any reported hole/electron centroids, separation, overlap, spread,
charge-transfer length, or related descriptor with its precise definition and
unit. Test grid and coefficient-threshold sensitivity. A colored cube or
separated centroid is a representation of the chosen state, not by itself proof
of a reaction mechanism or quantitative transferred charge.

An exciton-binding-energy estimate inherits strong method and dielectric/
environment assumptions. Report it only under the manual's applicable route
and with those limitations; do not infer it solely from orbital or excitation
energy differences.

## Assign peaks or states with a traceable table

Use a row-oriented table rather than prose-only assignments:

| Field | Required content |
|---|---|
| `source_state_id` | exact producer state/mode number and spin/symmetry label |
| `raw_position` | energy, wavelength, frequency, or shielding with unit |
| `raw_strength` | oscillator/rotatory strength, IR intensity, Raman activity, etc., with unit/convention |
| `analysis_parameters` | kernel, FWHM, scaling, temperature, representation, energy zero |
| `composition` | configurations, orbitals, fragments, or mode atoms under an explicit method |
| `closure` | coefficient normalization, hole/electron integrals, projected-weight sum, or parser count |
| `assignment` | bounded interpretation and comparison reference |
| `limitations` | truncation, basis dependence, overlap, origin dependence, parser/version boundary |

Separate raw transition data, processed curve, and figure hashes in the
artifact manifest.

## Troubleshoot before interpreting

| Symptom | Tests | Status |
|---|---|---|
| DOS peak moves when only FWHM changes | inspect raw levels and convolution sampling | representation-dependent; report raw energy |
| PDOS weights do not sum | basis mapping, fragment completeness, diffuse-basis instability, spin channel | technical failure until explained |
| Program parses zero/few transitions | exact producer/version, job completion, parser route, text units/schema | parser/input mismatch; do not plot |
| Raman shape disagrees after version change | program date, CP2K parser-fix boundary, temperature/incident frequency, activity vs intensity | reprocess under one pinned protocol |
| ECD sign differs | representation, coordinate origin, state order, rotatory-strength unit, enantiomer geometry | unresolved until conventions match |
| NMR shift offset is wrong | shielding/shift confusion, reference method, solvent, scaling, conformer weights | model/reference mismatch |
| Hole/electron integrals are far from one | truncated coefficients, mismatched files, small/coarse grid, wrong state/spin | scientific output blocked |
| State character changes between files | geometry/restart/state-order mismatch or near-degenerate root flipping | rebuild exact lineage; do not join sources by index alone |

Exit zero and a plotted curve establish neither parser completeness nor
scientific support. Require raw-source agreement, numerical closure,
parameter sensitivity, and a claim compatible with the selected representation.
