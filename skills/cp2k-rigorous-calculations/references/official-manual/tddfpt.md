# CP2K official manual snapshot: tddfpt

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/PROPERTIES/TDDFPT.html
- Raw SHA-256: 318c22758b42349f3cd6737d5a6c5ec9432335542bec2959e5bcd6d326efa174
- Status: version-matched cached official text; reopen the source for current live verification.

TDDFPT



References:

Iannuzzi2005

,

Hanasaki2025

,

HernandezSegura2025

Controls time-dependent density functional perturbation theory (TDDFPT) calculations for electronic excitations and related properties.

[

Edit on GitHub

]

Subsections

DIPOLE_MOMENTS

LINRES

LRIGPW

MGRID

PRINT

REDUCED_EXCITATION_SPACE

SOC

STDA

XC

Keywords



SECTION_PARAMETERS

ADMM_KERNEL_CORRECTION_SYMMETRIC

ADMM_KERNEL_XC_CORRECTION

AUTO_BASIS

CONVERGENCE

DIRECTIONAL_EXCITON_DESCRIPTORS

DO_BSE

DO_BSE_GW_ONLY

DO_BSE_W_ONLY

DO_LRIGPW

DO_SMEARING

EOS_SHIFT

EV_SHIFT

EXCITON_DESCRIPTORS

KERNEL

MAX_ITER

MAX_KV

MIN_AMPLITUDE

NLUMO

NPROC_STATE

NSTATES

OE_CORR

ORTHOGONAL_EPS

RESTART

RKS_TRIPLETS

SPINFLIP

WFN_RESTART_FILE_NAME

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

Activates the TDDFPT procedure.

[

Edit on GitHub

]

ADMM_KERNEL_CORRECTION_SYMMETRIC

:

logical

=

T



Lone keyword:

T

ADMM correction functional in kernel is applied symmetrically. Original implementation is using a non-symmetric formula.

[

Edit on GitHub

]

ADMM_KERNEL_XC_CORRECTION

:

logical

=

T



Lone keyword:

T

Use/Ignore ADMM correction xc functional for TD kernel. XC correction functional is defined in ground state XC section.

[

Edit on GitHub

]

AUTO_BASIS

:

string[

]

=

X



Keyword can be repeated.

Usage:

AUTO_BASIS {basis_type} {basis_size}

Specify size of automatically generated auxiliary basis sets: Options={small,medium,large,huge}

[

Edit on GitHub

]

CONVERGENCE

:

real

=

1.00000000E-005

[hartree]



Mentions:

⭐

Time-Dependent DFT

Target accuracy for excited state energies.

[

Edit on GitHub

]

DIRECTIONAL_EXCITON_DESCRIPTORS

:

logical

=

F



Print cartesian components of exciton descriptors.

[

Edit on GitHub

]

DO_BSE

:

logical

=

F



Lone keyword:

T

Usage:

DO_BSE

Choosing BSE kernel.

[

Edit on GitHub

]

DO_BSE_GW_ONLY

:

logical

=

F



Lone keyword:

T

Usage:

DO_BSE_GW_ONLY

Debug option for BSE kernel.

[

Edit on GitHub

]

DO_BSE_W_ONLY

:

logical

=

F



Lone keyword:

T

Usage:

DO_BSE_W_ONLY

Debug option for BSE kernel.

[

Edit on GitHub

]

DO_LRIGPW

:

logical

=

F



Local resolution of identity for Coulomb contribution.

[

Edit on GitHub

]

DO_SMEARING

:

logical

=

F



Lone keyword:

T

Implying smeared occupation.

[

Edit on GitHub

]

EOS_SHIFT

:

real

=

0.00000000E+000

[eV]



Aliases:

OPEN_SHELL_SHIFT

Usage:

EOS_SHIFT 0.200

Constant shift of open shell eigenvalues.

[

Edit on GitHub

]

EV_SHIFT

:

real

=

0.00000000E+000

[eV]



Aliases:

VIRTUAL_SHIFT

Usage:

EV_SHIFT 0.500

Mentions:

⭐

Time-Dependent DFT

Constant shift of virtual state eigenvalues.

[

Edit on GitHub

]

EXCITON_DESCRIPTORS

:

logical

=

F



Compute exciton descriptors. Details given in Manual section about Bethe Salpeter equation.

[

Edit on GitHub

]

KERNEL

:

enum

=

FULL



Usage:

KERNEL FULL

Valid values:

FULL

STDA

NONE

Mentions:

⭐

Time-Dependent DFT

Options to compute the kernel

[

Edit on GitHub

]

MAX_ITER

:

integer

=

50



Maximal number of iterations to be performed.

[

Edit on GitHub

]

MAX_KV

:

integer

=

5000



Maximal number of Krylov space vectors. Davidson iterations will be restarted upon reaching this limit.

[

Edit on GitHub

]

MIN_AMPLITUDE

:

real

=

5.00000000E-002



Mentions:

⭐

Time-Dependent DFT

The smallest excitation amplitude to print.

[

Edit on GitHub

]

NLUMO

:

integer

=

-1



Mentions:

⭐

Time-Dependent DFT

Number of unoccupied orbitals to consider. Default is to use all unoccupied orbitals (-1).

[

Edit on GitHub

]

NPROC_STATE

:

integer

=

0



Number of MPI processes to be used per excited state. Default is to use all MPI processes (0).

[

Edit on GitHub

]

NSTATES

:

integer

=

1



Mentions:

⭐

Time-Dependent DFT

Number of excited states to converge.

[

Edit on GitHub

]

OE_CORR

:

enum

=

NONE



Valid values:

NONE

No orbital correction scheme is used

LB94

van Leeuwen and Baerends. PRA, 49:2421, 1994

GLLB

Gritsenko, van Leeuwen, van Lenthe, Baerends. PRA, 51:1944, 1995

SAOP

Gritsenko, Schipper, Baerends. Chem. Phys. Lett., 302:199, 1999

SHIFT

Constant shift of virtual and/or open-shell orbitals

Orbital energy correction potential.

[

Edit on GitHub

]

ORTHOGONAL_EPS

:

real

=

1.00000000E-004



The largest possible overlap between the ground state and orthogonalised excited state wave-functions. Davidson iterations will be restarted when the overlap goes beyond this threshold in order to prevent numerical instability.

[

Edit on GitHub

]

RESTART

:

logical

=

F



Lone keyword:

T

Mentions:

⭐

Time-Dependent DFT

Restart the TDDFPT calculation if a restart file exists

[

Edit on GitHub

]

RKS_TRIPLETS

:

logical

=

F



Mentions:

⭐

Time-Dependent DFT

Compute triplet excited states using spin-unpolarised molecular orbitals.

[

Edit on GitHub

]

SPINFLIP

:

enum

=

NONE



Usage:

SPINFLIP NONCOLLINEAR

Valid values:

NONE

Only molecular orbital energy differences are considered

COLLINEAR

MO energy diferences and Fock exchange contributions are considered

NONCOLLINEAR

MO energy differences, Fock exchange and Noncollinear local exchange-correlation kernel are considered

References:

HernandezSegura2025

Selects the type of spin-flip TDDFPT kernel

[

Edit on GitHub

]

WFN_RESTART_FILE_NAME

:

string



Aliases:

RESTART_FILE_NAME

Usage:

WFN_RESTART_FILE_NAME

Mentions:

⭐

Time-Dependent DFT

Name of the wave function restart file, may include a path. If no file is specified, the default is to open the file as generated by the wave function restart print key.

[

Edit on GitHub

]
