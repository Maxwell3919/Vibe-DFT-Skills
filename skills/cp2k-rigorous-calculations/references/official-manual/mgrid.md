# CP2K official manual snapshot: mgrid

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/MGRID.html
- Raw SHA-256: e4780f367dd1716fd4645893695016e14fe539b826ba7b4168d0941e8ce4b578
- Status: version-matched cached official text; reopen the source for current live verification.

MGRID



Controls the multigrid used by GPW/GAPW to represent densities, potentials, and Gaussian products on real-space grids.

[

Edit on GitHub

]

Subsections

INTERPOLATOR

RS_GRID

Keywords



COMMENSURATE

CUTOFF

MULTIGRID_CUTOFF

MULTIGRID_SET

NGRIDS

PROGRESSION_FACTOR

REALSPACE

REL_CUTOFF

SKIP_LOAD_BALANCE_DISTRIBUTED

Keyword descriptions



COMMENSURATE

:

logical

=

F



Lone keyword:

T

Usage:

commensurate

If the grids should be commensurate. If true overrides the progression factor and the cutoffs of the sub grids

[

Edit on GitHub

]

CUTOFF

:

real

=

2.80000000E+002

[Ry]



Usage:

cutoff 300

Mentions:

⭐

Run a First Calculation

, ⭐

Troubleshooting

, ⭐

Basis Sets

, ⭐

How to make a SCF run converge

, ⭐

How to Converge the CUTOFF and REL_CUTOFF

, ⭐

Gaussian Augmented Plane Waves

, ⭐

Geometry and cell optimization

, ⭐

Molecular Dynamics

Plane-wave cutoff of the finest real-space grid level. Increasing this value improves the grid representation, but it is not a substitute for converging the Gaussian basis set. Default value for SE or DFTB calculation is 1.0 [Ry].

[

Edit on GitHub

]

MULTIGRID_CUTOFF

:

real[

]

=

[Ry]



Aliases:

CUTOFF_LIST

Usage:

MULTIGRID_CUTOFF 200.0 100.0

List of cutoff values to set up multigrids manually

[

Edit on GitHub

]

MULTIGRID_SET

:

logical

=

F



Usage:

MULTIGRID_SET

Activate a manual setting of the multigrids

[

Edit on GitHub

]

NGRIDS

:

integer

=

4



Usage:

ngrids 1

Mentions:

⭐

How to Converge the CUTOFF and REL_CUTOFF

Number of multigrid levels. Smooth Gaussian products can be mapped to coarser levels, while sharper products require finer levels.

[

Edit on GitHub

]

PROGRESSION_FACTOR

:

real

=

3.00000000E+000



Usage:

progression_factor

Mentions:

⭐

How to Converge the CUTOFF and REL_CUTOFF

Factor used to derive the cutoff of coarser multigrid levels when they are not given explicitly.

[

Edit on GitHub

]

REALSPACE

:

logical

=

F



Lone keyword:

T

Usage:

realspace

If both rho and rho_gspace are needed

[

Edit on GitHub

]

REL_CUTOFF

:

real

=

4.00000000E+001

[Ry]



Aliases:

RELATIVE_CUTOFF

Usage:

RELATIVE_CUTOFF real

Mentions:

⭐

Run a First Calculation

, ⭐

How to make a SCF run converge

, ⭐

How to Converge the CUTOFF and REL_CUTOFF

, ⭐

Geometry and cell optimization

, ⭐

Molecular Dynamics

Controls to which multigrid level a Gaussian product is mapped. It is the reference cutoff for a Gaussian with exponent alpha=1. Larger values keep more Gaussian products on finer grids and can be important for accurate energies, forces, stress tensors, and variable-cell simulations.

[

Edit on GitHub

]

SKIP_LOAD_BALANCE_DISTRIBUTED

:

logical

=

F



Lone keyword:

T

Usage:

SKIP_LOAD_BALANCE_DISTRIBUTED

Skips load balancing on distributed multigrids. Memory usage is O(p) so may be used for all but the very largest runs.

[

Edit on GitHub

]
