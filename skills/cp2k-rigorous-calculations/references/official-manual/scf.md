# CP2K official manual snapshot: scf

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF.html
- Raw SHA-256: f7bfeb7d25276eb167788547f679bd593f78352b744bd59fe351999367349ad6
- Status: version-matched cached official text; reopen the source for current live verification.

SCF



Parameters needed to perform an SCF run.

[

Edit on GitHub

]

Subsections

DIAGONALIZATION

GCE

MIXING

MOM

OT

OUTER_SCF

PRINT

SMEAR

Keywords



ADDED_MOS

CHOLESKY

EPS_DIIS

EPS_EIGVAL

EPS_LUMO

EPS_SCF

EPS_SCF_HISTORY

FORCE_SCF_CALCULATION

IGNORE_CONVERGENCE_FAILURE

LEVEL_SHIFT

MAX_DIIS

MAX_ITER_LUMO

MAX_SCF

MAX_SCF_HISTORY

NCOL_BLOCK

NROW_BLOCK

ROKS_F

ROKS_PARAMETERS

ROKS_SCHEME

SCF_GUESS

Keyword descriptions



ADDED_MOS

:

integer[

]

=

0



Usage:

ADDED_MOS

Mentions:

⭐

Density of States

, ⭐

Molecular orbitals output

Number of additional molecular orbitals added for each spin channel. This is commonly needed for smearing, excited-state, or post-Hartree-Fock calculations. Use -1 to add all available orbitals.

[

Edit on GitHub

]

CHOLESKY

:

enum

=

RESTORE



Usage:

CHOLESKY REDUCE

Valid values:

OFF

The cholesky algorithm is not used

REDUCE

Reduce is called

RESTORE

Reduce is replaced by two restore

INVERSE

Restore uses operator multiply by inverse of the triangular matrix

INVERSE_DBCSR

Like inverse, but matrix stored as dbcsr, sparce matrix algebra used when possible

If the cholesky method should be used for computing the inverse of S, and in this case calling which Lapack routines

[

Edit on GitHub

]

EPS_DIIS

:

real

=

1.00000000E-001



Usage:

EPS_DIIS 5.0e-2

Threshold on the convergence to start using DIAG/DIIS or OT/DIIS. Default for OT/DIIS is never to switch.

[

Edit on GitHub

]

EPS_EIGVAL

:

real

=

1.00000000E-005



Usage:

EPS_EIGVAL 1.0

Throw away linear combinations of basis functions with a small eigenvalue in S

[

Edit on GitHub

]

EPS_LUMO

:

real

=

1.00000000E-005



Aliases:

EPS_LUMOS

Usage:

EPS_LUMO 1.0E-6

Target accuracy for the calculation of the LUMO energies with the OT eigensolver.

[

Edit on GitHub

]

EPS_SCF

:

real

=

1.00000000E-005



Usage:

EPS_SCF 1.e-6

Mentions:

⭐

How to make a SCF run converge

, ⭐

Geometry and cell optimization

, ⭐

Molecular Dynamics

, ⭐

Monte Carlo

Target convergence threshold for the inner SCF cycle.

[

Edit on GitHub

]

EPS_SCF_HISTORY

:

real

=

0.00000000E+000



Aliases:

EPS_SCF_HIST

Lone keyword:

1.00000000E-005

Usage:

EPS_SCF_HISTORY 1.e-5

Target accuracy for the SCF convergence after the history pipeline is filled.

[

Edit on GitHub

]

FORCE_SCF_CALCULATION

:

logical

=

F



Lone keyword:

T

Usage:

FORCE_SCF_CALCULATION logical_value

Request a SCF type solution even for nonSCF methods.

[

Edit on GitHub

]

IGNORE_CONVERGENCE_FAILURE

:

logical

=

F



Lone keyword:

T

Usage:

IGNORE_CONVERGENCE_FAILURE logical_value

Mentions:

⭐

How to make a SCF run converge

If true, only a warning is issued if an SCF iteration has not converged. By default, a run is aborted if the required convergence criteria have not been achieved.

[

Edit on GitHub

]

LEVEL_SHIFT

:

real

=

0.00000000E+000

[hartree]



Aliases:

LSHIFT

Usage:

LEVEL_SHIFT 0.1

Use level shifting to improve convergence

[

Edit on GitHub

]

MAX_DIIS

:

integer

=

4



Aliases:

MAX_DIIS_BUFFER_SIZE

Usage:

MAX_DIIS 3

Maximum number of DIIS vectors to be used

[

Edit on GitHub

]

MAX_ITER_LUMO

:

integer

=

299



Aliases:

MAX_ITER_LUMOS

Usage:

MAX_ITER_LUMO 100

Maximum number of iterations for the calculation of the LUMO energies with the OT eigensolver.

[

Edit on GitHub

]

MAX_SCF

:

integer

=

50



Usage:

MAX_SCF 200

Mentions:

⭐

How to make a SCF run converge

, ⭐

Monte Carlo

Maximum number of inner SCF iterations for one electronic optimization.

[

Edit on GitHub

]

MAX_SCF_HISTORY

:

integer

=

0



Aliases:

MAX_SCF_HIST

Lone keyword:

1

Usage:

MAX_SCF_HISTORY 1

Maximum number of SCF iterations after the history pipeline is filled

[

Edit on GitHub

]

NCOL_BLOCK

:

integer

=

32



Usage:

NCOL_BLOCK 31

Sets the number of columns in a scalapack block

[

Edit on GitHub

]

NROW_BLOCK

:

integer

=

32



Usage:

NROW_BLOCK 31

sets the number of rows in a scalapack block

[

Edit on GitHub

]

ROKS_F

:

real

=

5.00000000E-001



Aliases:

F_ROKS

Usage:

ROKS_F 1/2

Allows to define the parameter f for the general ROKS scheme.

[

Edit on GitHub

]

ROKS_PARAMETERS

:

real

[

6

]

=

-5.00000000E-001

1.50000000E+000

5.00000000E-001

1.50000000E+000

-5.00000000E-001



Aliases:

ROKS_PARAMETER

Usage:

ROKS_PARAMETERS 1/2 1/2 1/2 1/2 1/2 1/2

Allows to define all parameters for the high-spin ROKS scheme explicitly. The full set of 6 parameters has to be specified in the order acc, bcc, aoo, boo, avv, bvv

[

Edit on GitHub

]

ROKS_SCHEME

:

enum

=

HIGH-SPIN



Usage:

ROKS_SCHEME HIGH-SPIN

Valid values:

GENERAL

HIGH-SPIN

Selects the ROKS scheme when ROKS is applied.

[

Edit on GitHub

]

SCF_GUESS

:

enum

=

ATOMIC



Usage:

SCF_GUESS RESTART

Valid values:

ATOMIC

Generate an atomic density using the atomic code and internal default values

RESTART

Use the RESTART file as an initial guess (and ATOMIC if not present).

RANDOM

Use random wavefunction coefficients.

CORE

Diagonalize the core hamiltonian for an initial guess.

HISTORY_RESTART

Extrapolated from previous RESTART files.

MOPAC

Use same guess as MOPAC for semi-empirical methods or a simple diagonal density matrix for other methods

EHT

Use the EHT (gfn0-xTB) code to generate an initial wavefunction.

SPARSE

Generate a sparse wavefunction using the atomic code (for OT based methods)

NONE

Skip initial guess (only for non-self consistent methods).

Mentions:

⭐

How to make a SCF run converge

Selects how the initial wavefunction or density matrix is generated.

[

Edit on GitHub

]
