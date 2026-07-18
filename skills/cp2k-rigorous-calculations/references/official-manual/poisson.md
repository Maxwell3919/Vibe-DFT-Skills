# CP2K official manual snapshot: poisson

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/POISSON.html
- Raw SHA-256: 859bf837154f3bd382984e7fbc4aa73665b0f59991f1bfc611b3456de67de401
- Status: version-matched cached official text; reopen the source for current live verification.

POISSON



Controls the Poisson solver and electrostatic boundary conditions used by DFT.

[

Edit on GitHub

]

Subsections

EWALD

IMPLICIT

MT

MULTIPOLE

WAVELET

Keywords



PERIODIC

POISSON_SOLVER

Keyword descriptions



PERIODIC

:

enum

=

XYZ



Usage:

PERIODIC (x|y|z|xy|xz|yz|xyz|none)

Valid values:

X

Y

Z

XY

XZ

YZ

XYZ

NONE

Specifies the directions in which periodic boundary conditions apply to electrostatics. See the CELL section for the periodicity used by geometry and pair lists; the settings are usually the same.

[

Edit on GitHub

]

POISSON_SOLVER

:

enum

=

PERIODIC



Aliases:

POISSON ,PSOLVER

Usage:

POISSON_SOLVER char

Valid values:

PERIODIC

PERIODIC is only available for fully (3D) periodic systems.

ANALYTIC

ANALYTIC is available for 0D, 1D and 2D periodic solutions using analytical green functions in the g space (slow convergence).

MT

MT (Martyna Tuckermann) decoupling that interacts only with the nearest neighbor. Beware results are completely wrong if the cell is smaller than twice the cluster size (with electronic density). Available for 0D and 2D systems.

MULTIPOLE

MULTIPOLE uses a scheme that fits the total charge with one gaussian per atom. Available only for cluster (0D) systems.

WAVELET

WAVELET allows for 0D, 2D and 3D systems. For 2D systems all PERIODIC XY, XZ and YZ combinations are accepted. It does not require very large unit cells, only that the density goes to zero on the faces of the cell. The use of PREFERRED_FFT_LIBRARY FFTSG is required.

IMPLICIT

IMPLICIT allows for 0D, 1D, 2D and 3D systems.

References:

Blöchl1995

,

Martyna1999

,

Genovese2006

,

Genovese2007

Specify which kind of solver to use to solve the Poisson equation.

[

Edit on GitHub

]
