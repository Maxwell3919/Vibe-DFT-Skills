# CP2K official manual snapshot: gapw-method

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/gapw.html
- Raw SHA-256: 4fc6069a0f5ab929e2278b30da8df418e82700a12b56cbdef571cea268ff0f7b
- Status: version-matched cached official text; reopen the source for current live verification.

Gaussian Augmented Plane Waves



The Gaussian augmented plane wave (

GAPW

) method extends GPW so that all-electron

calculations and calculations with very small-core pseudopotentials become practical in CP2K. The

central idea is to keep the smooth part of the density on the regular GPW grids while treating the

rapidly varying density close to the nuclei with atom-centered contributions.

GAPW is useful when the core electron density matters, for example in all-electron calculations,

core-level spectroscopy, magnetic properties, and some small-core pseudopotential setups. For

standard valence-only pseudopotential DFT calculations, GPW is usually simpler and faster.

Activating GAPW



GAPW is activated in the

QS

section:

&FORCE_EVAL

METHOD Quickstep

&DFT

&QS

METHOD GAPW

&END QS

&END DFT

&END FORCE_EVAL

All-electron GAPW calculations also require all-electron basis sets and

POTENTIAL

ALL

for the

corresponding atomic kinds:

&KIND O

BASIS_SET SVP-MOLOPT-GGA-ae

POTENTIAL ALL

LEBEDEV_GRID 110

RADIAL_GRID 80

&END KIND

A complete tested water example is available as

gapw_h2o.inp

. It is intentionally small and is

meant as a starting point rather than as a production-quality benchmark.

Accuracy Parameters



Several GAPW-specific tolerances control the split between soft grid-based and hard atom-centered

contributions:

EPSFIT

controls how Gaussian exponents are split into the

hard and soft parts. Lowering it includes harder functions in the soft density and usually

requires a larger

CUTOFF

.

EPSRHO0

controls the range used for the hard compensation

density contribution.

EPSSVD

controls the singular value decomposition tolerance

used for projector matrices.

The atom-centered integration grid is controlled per kind with

LEBEDEV_GRID

and

RADIAL_GRID

. Increasing these values can improve

the electron count and the accuracy of properties that depend on the near-core density, but it also

increases cost.

Practical Guidance



When setting up a GAPW calculation:

Use an all-electron basis set for

POTENTIAL

ALL

, or a basis set designed for the chosen

small-core pseudopotential.

Inspect the electron count printed by CP2K after SCF convergence. It is a useful diagnostic for

the quality of the hard/soft density split.

Tighten

EPSFIT

,

EPSRHO0

,

EPSSVD

, and the atomic grids only as much as needed for the target

property.

Increase the density

CUTOFF

when harder Gaussian

exponents are included in the soft density.

Prefer GPW when the calculation does not need all-electron or near-core accuracy.

See Also



Lippert1999

Krack2000

Iannuzzi2026
