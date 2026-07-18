# CP2K official manual snapshot: qmmm

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/QMMM.html
- Raw SHA-256: 88e6bcdbca17648050d81004bc3fd773f06eafe8d4c17173704140e4d036848f
- Status: version-matched cached official text; reopen the source for current live verification.

QMMM



References:

Laino2005

,

Laino2006

Controls QM/MM calculations, including mechanical, electrostatic, Gaussian-expanded, and periodic embedding options.

[

Edit on GitHub

]

Subsections

CELL

FORCEFIELD

FORCE_MIXING

IMAGE_CHARGE

INTERPOLATOR

LINK

MM_KIND

PERIODIC

PRINT

QM_KIND

WALLS

Keywords



CENTER

CENTER_GRID

CENTER_TYPE

DELTA_CHARGE

EPS_MM_RSPACE

E_COUPL

INITIAL_TRANSLATION_VECTOR

MM_POTENTIAL_FILE_NAME

NOCOMPATIBILITY

PARALLEL_SCHEME

SPHERICAL_CUTOFF

USE_GEEP_LIB

Keyword descriptions



CENTER

:

enum

=

EVERY_STEP



Usage:

center (EVERY_STEP|SETUP_ONLY|NEVER)

Valid values:

EVERY_STEP

Re-center every step

SETUP_ONLY

Center at first step only

NEVER

Never center

This keyword sets when the QM system is automatically centered. Default is EVERY_STEP.

[

Edit on GitHub

]

CENTER_GRID

:

logical

=

F



Usage:

CENTER_GRID LOGICAL

This keyword specifies whether the QM system is centered in units of the grid spacing.

[

Edit on GitHub

]

CENTER_TYPE

:

enum

=

MAX_MINUS_MIN



Usage:

center_type (MAX_MINUS_MIN|PBC_AWARE_MAX_MINUS_MIN)

Valid values:

MAX_MINUS_MIN

Center of box defined by maximum coordinate minus minimum coordinate

PBC_AWARE_MAX_MINUS_MIN

PBC-aware centering (useful for &QMMM&FORCE_MIXING)

This keyword specifies how to do the QM system centering.

[

Edit on GitHub

]

DELTA_CHARGE

:

integer

=

0



Usage:

DELTA_CHARGE q

Additional net charge relative to that specified in DFT section. Used automatically by force mixing

[

Edit on GitHub

]

EPS_MM_RSPACE

:

real

=

1.00000000E-010



Usage:

eps_mm_rspace real

Set the threshold for the collocation of the GEEP gaussian functions. this keyword affects only the GAUSS E_COUPLING.

[

Edit on GitHub

]

E_COUPL

:

enum

=

NONE



Aliases:

QMMM_COUPLING ,ECOUPL

Usage:

E_COUPL GAUSS

Valid values:

NONE

Mechanical coupling (i.e. classical point charge based)

COULOMB

Using analytical 1/r potential (Coulomb) - not available for GPW/GAPW

GAUSS

Using fast Gaussian expansion of the electrostatic potential (Erf(r/rc)/r) - not available for DFTB.

S-WAVE

Using fast Gaussian expansion of the s-wave electrostatic potential

POINT_CHARGE

Using quantum mechanics derived point charges interacting with MM charges

Mentions:

⭐

QM/MM with Built-in Force Field

Selects the QM-MM coupling model used for the electrostatic interaction.

[

Edit on GitHub

]

INITIAL_TRANSLATION_VECTOR

:

real

[

3

]

=

0.00000000E+000



Usage:

initial_translation_vector

This keyword specify the initial translation vector to be applied to the system.

[

Edit on GitHub

]

MM_POTENTIAL_FILE_NAME

:

string

=

MM_POTENTIAL



Usage:

MM_POTENTIAL_FILE_NAME {filename}

Name of the file containing the potential expansion in gaussians. See the USE_GEEP_LIB keyword.

[

Edit on GitHub

]

NOCOMPATIBILITY

:

logical

=

F



Lone keyword:

T

Usage:

nocompatibility LOGICAL

This keyword disables the compatibility of QM/MM potential between CPMD and CP2K implementations. The compatibility is achieved using an MM potential of the form: Erf[x/rc]/x + (1/rc -2/(pi^1/2*rc))*Exp[-(x/rc)^2]. This keyword has effect only selecting GAUSS E_COUPLING type.

[

Edit on GitHub

]

PARALLEL_SCHEME

:

enum

=

ATOM



Usage:

parallel_scheme (ATOM|GRID)

Valid values:

ATOM

parallelizes on atoms. grids replicated. Replication of the grids can be quite expensive memory wise if running on a system with limited memory per core. The grid option may be preferred in this case.

GRID

parallelizes on grid slices. atoms replicated.

Chooses the parallel_scheme for the long range Potential

[

Edit on GitHub

]

SPHERICAL_CUTOFF

:

real

[

2

]

=

-5.29177209E-001

0.00000000E+000

[angstrom]



Usage:

SPHERICAL_CUTOFF

Set the spherical cutoff for the QMMM electrostatic interaction. This acts like a charge multiplicative factor dependent on cutoff. For MM atoms farther than the SPHERICAL_CUTOFF(1) their charge is zero. The switch is performed with a smooth function: 0.5*(1-TANH((r-[SPH_CUT(1)-20*SPH_CUT(2)])/(SPH_CUT(2)))). Two values are required: the first one is the distance cutoff. The second one controls the stiffness of the smoothing.

[

Edit on GitHub

]

USE_GEEP_LIB

:

integer

=

0



Usage:

use_geep_lib INTEGER

This keyword enables the use of the internal GEEP library to generate the gaussian expansion of the MM potential. Using this keyword there’s no need to provide the MM_POTENTIAL_FILENAME. It expects a number from 2 to 15 (the number of gaussian functions to be used in the expansion.

[

Edit on GitHub

]
