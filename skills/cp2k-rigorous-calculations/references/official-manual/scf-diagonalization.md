# CP2K official manual snapshot: scf-diagonalization

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/DIAGONALIZATION.html
- Raw SHA-256: ce2e520745231e2561e831a52100cad1798e40f0e20de00a40db1cdf7cf204b4
- Status: version-matched cached official text; reopen the source for current live verification.

DIAGONALIZATION



Set up type and parameters for Kohn-Sham matrix diagonalization.

[

Edit on GitHub

]

Subsections

DAVIDSON

DIAG_SUB_SCF

FILTER_MATRIX

KRYLOV

OT

Keywords



SECTION_PARAMETERS

ALGORITHM

EPS_ADAPT

EPS_ITER

EPS_JACOBI

JACOBI_THRESHOLD

MAX_ITER

Keyword descriptions



SECTION_PARAMETERS

:

logical

=

F



Lone keyword:

T

Usage:

&DIAGONALIZATION T

controls the activation of the diagonalization method

[

Edit on GitHub

]

ALGORITHM

:

enum

=

STANDARD



Usage:

ALGORITHM STANDARD

Valid values:

STANDARD

Standard diagonalization: LAPACK methods or Jacobi.

OT

Iterative diagonalization using OT method

LANCZOS

Block Krylov-space approach to self-consistent diagonalisation

DAVIDSON

Preconditioned blocked Davidson

FILTER_MATRIX

Filter matrix diagonalization

Algorithm to be used for diagonalization

[

Edit on GitHub

]

EPS_ADAPT

:

real

=

0.00000000E+000



Usage:

EPS_ADAPT 0.01

Required accuracy in iterative diagonalization as compared to current SCF convergence

[

Edit on GitHub

]

EPS_ITER

:

real

=

1.00000000E-008



Usage:

EPS_ITER 1.e-8

Required accuracy in iterative diagonalization

[

Edit on GitHub

]

EPS_JACOBI

:

real

=

0.00000000E+000



Usage:

EPS_JACOBI 1.0E-5

References:

Stewart1982

Below this threshold value for the SCF convergence the pseudo-diagonalization method using Jacobi rotations is activated. This method is much faster than a real diagonalization and it is even speeding up while achieving full convergence. However, it needs a pre-converged wavefunction obtained by at least one real diagonalization which is further optimized while keeping the original eigenvalue spectrum. The MO eigenvalues are NOT updated. The method might be useful to speed up calculations for large systems e.g. using a semi-empirical method.

[

Edit on GitHub

]

JACOBI_THRESHOLD

:

real

=

1.00000000E-007



Usage:

JACOBI_THRESHOLD 1.0E-6

References:

Stewart1982

Controls the accuracy of the pseudo-diagonalization method using Jacobi rotations

[

Edit on GitHub

]

MAX_ITER

:

integer

=

2



Usage:

MAX_ITER 20

Maximum number of iterations in iterative diagonalization

[

Edit on GitHub

]
