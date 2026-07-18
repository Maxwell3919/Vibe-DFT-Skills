# CP2K official manual snapshot: transport

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/TRANSPORT.html
- Raw SHA-256: 96865ca920fb063a1a96358fdd7fd7a07d50f069326b23aa391b59ec216ff573
- Status: version-matched cached official text; reopen the source for current live verification.

TRANSPORT



References:

Bruck2014

Specifies the parameters for transport, sets parameters for the OMEN code, see also

https://nano-tcad.ee.ethz.ch

.

[

Edit on GitHub

]

Subsections

BEYN

CONTACT

PEXSI

PRINT

Keywords



COLZERO_THRESHOLD

CONTACT_FILLING

CSR_SCREENING

CUTOUT

DENSITY_MIXING

ENERGY_INTERVAL

EPS_DECAY

EPS_EIGVAL_DEGEN

EPS_FERMI

EPS_LIMIT

EPS_LIMIT_CC

EPS_MU

EPS_SINGULARITY_CURVATURES

GPUS_PER_POINT

INJECTION_METHOD

LINEAR_SOLVER

MATRIX_INVERSION_METHOD

MIN_INTERVAL

NUM_INTERVAL

NUM_POLE

N_KPOINTS

N_POINTS_INV

OBC_EQUILIBRIUM

QT_FORMALISM

REAL_AXIS_INTEGRATION_METHOD

TASKS_PER_ENERGY_POINT

TASKS_PER_POLE

TEMPERATURE

TRANSPORT_METHOD

Keyword descriptions



COLZERO_THRESHOLD

:

real

=

1.00000000E-012



Usage:

COLZERO_THRESHOLD

The smallest number that is not zero in the full diagonalization part.

[

Edit on GitHub

]

CONTACT_FILLING

:

enum

=

BAND_STRUCTURE



Valid values:

BAND_STRUCTURE

Determine the Fermi levels from the band structure.

DOS

Determine the Fermi levels from the density of states.

Determination of the contact Fermi levels. Note that this keyword only works when the TRANSPORT_METHOD is specified as TRANSPORT.

[

Edit on GitHub

]

CSR_SCREENING

:

logical

=

T



Lone keyword:

T

Whether distance screening should be applied to improve sparsity of CSR matrices.

[

Edit on GitHub

]

CUTOUT

:

integer

[

2

]

=

0



Usage:

CUTOUT

The number of atoms at the beginning and the end of the structure where the density should not be changed.

[

Edit on GitHub

]

DENSITY_MIXING

:

real

=

1.00000000E+000



Usage:

DENSITY_MIXING

Mixing parameter for a density mixing in OMEN.

[

Edit on GitHub

]

ENERGY_INTERVAL

:

real

=

1.00000000E-003



Usage:

ENERGY_INTERVAL

Distance between energy points in eV.

[

Edit on GitHub

]

EPS_DECAY

:

real

=

1.00000000E-004



Usage:

EPS_DECAY

The smallest imaginary part that a decaying eigenvalue may have not to be considered as propagating.

[

Edit on GitHub

]

EPS_EIGVAL_DEGEN

:

real

=

1.00000000E-006



Usage:

EPS_EIGVAL_DEGEN

Filter for degenerate bands in the injection vector.

[

Edit on GitHub

]

EPS_FERMI

:

real

=

0.00000000E+000



Usage:

EPS_FERMI

Cutoff for the tail of the Fermi function.

[

Edit on GitHub

]

EPS_LIMIT

:

real

=

1.00000000E-004



Usage:

EPS_LIMIT

The smallest eigenvalue that is kept.

[

Edit on GitHub

]

EPS_LIMIT_CC

:

real

=

1.00000000E-006



Usage:

EPS_LIMIT_CC

The smallest eigenvalue that is kept on the complex contour.

[

Edit on GitHub

]

EPS_MU

:

real

=

1.00000000E-006



Usage:

EPS_MU

Accuracy to which the Fermi level should be determined.

[

Edit on GitHub

]

EPS_SINGULARITY_CURVATURES

:

real

=

1.00000000E-012



Usage:

EPS_SINGULARITY_CURVATURES

Filter for degenerate bands in the bandstructure.

[

Edit on GitHub

]

GPUS_PER_POINT

:

integer

=

2



Usage:

GPUS_PER_POINT

Number of GPUs per energy point for SplitSolve. Needs to be a power of two

[

Edit on GitHub

]

INJECTION_METHOD

:

enum

=

BEYN



Usage:

INJECTION_METHOD

Valid values:

EVP

Full eigenvalue solver.

BEYN

Beyn eigenvalue solver.

Method to solve the eigenvalue problem for the open boundary conditions.

[

Edit on GitHub

]

LINEAR_SOLVER

:

enum

=

FULL



Usage:

LINEAR_SOLVER

Valid values:

SPLITSOLVE

SUPERLU

MUMPS

FULL

BANDED

PARDISO

UMFPACK

Preferred solver for solving the linear system of equations.

[

Edit on GitHub

]

MATRIX_INVERSION_METHOD

:

enum

=

FULL



Usage:

MATRIX_INVERSION_METHOD

Valid values:

FULL

PEXSI

PARDISO

RGF

Preferred matrix inversion method.

[

Edit on GitHub

]

MIN_INTERVAL

:

real

=

1.00000000E-004



Usage:

MIN_INTERVAL

Smallest enery distance in energy vector.

[

Edit on GitHub

]

NUM_INTERVAL

:

integer

=

10



Usage:

NUM_INTERVAL

Max number of energy points per small interval.

[

Edit on GitHub

]

NUM_POLE

:

integer

=

64



Usage:

NUM_POLE

The number of terms in the PEXSI’s pole expansion method.

[

Edit on GitHub

]

N_KPOINTS

:

integer

=

64



Usage:

N_KPOINTS

The number of k points for determination of the singularities.

[

Edit on GitHub

]

N_POINTS_INV

:

integer

=

64



Usage:

N_POINTS_INV

Number of integration points for the sigma solver on the complex contour.

[

Edit on GitHub

]

OBC_EQUILIBRIUM

:

logical

=

F



Lone keyword:

T

Compute the equilibrium density with open boundary conditions.

[

Edit on GitHub

]

QT_FORMALISM

:

enum

=

QTBM



Usage:

QT_FORMALISM

Valid values:

NEGF

The non-equilibrium Green’s function formalism.

QTBM

The quantum transmitting boundary method / wave-function formalism.

Preferred quantum transport formalism to compute the current and density.

[

Edit on GitHub

]

REAL_AXIS_INTEGRATION_METHOD

:

enum

=

GAUSS_CHEBYSHEV



Usage:

REAL_AXIS_INTEGRATION_METHOD

Valid values:

GAUSS_CHEBYSHEV

Gauss-Chebyshev integration between singularity points.

TRAPEZOIDAL_RULE

Trapezoidal rule on the total range.

READ

Read integration points from a file (named E.dat).

Integration method for the real axis.

[

Edit on GitHub

]

TASKS_PER_ENERGY_POINT

:

integer

=

1



Usage:

TASKS_PER_ENERGY_POINT

Number of tasks per energy point. The value should be a divisor of the total number of MPI ranks.

[

Edit on GitHub

]

TASKS_PER_POLE

:

integer

=

1



Usage:

TASKS_PER_POLE

Number of tasks per pole in the pole expansion method. The value should be a divisor of the total number of MPI ranks.

[

Edit on GitHub

]

TEMPERATURE

:

real

=

3.00000000E+002

[K]



Usage:

TEMPERATURE [K] 300.0

Temperature.

[

Edit on GitHub

]

TRANSPORT_METHOD

:

enum

=

TRANSPORT



Usage:

TRANSPORT_METHOD

Valid values:

TRANSPORT

self-consistent CP2K and OMEN transport calculations

LOCAL_SCF

CP2K valence Hamiltonian + OMEN self-consistent calculations on conduction electrons

TRANSMISSION

self-consistent transmission calculations without applied bias voltage

Preferred method for transport calculations.

[

Edit on GitHub

]
