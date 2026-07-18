# CP2K official manual snapshot: admm

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html
- Raw SHA-256: 218089ffef6ff1fabac7d76e4a4fd61be6d79262a7889107f5011b771b1220f3
- Status: version-matched cached official text; reopen the source for current live verification.

AUXILIARY_DENSITY_MATRIX_METHOD



References:

Guidon2010

Controls the auxiliary density matrix method (ADMM), which evaluates Hartree-Fock exchange on a smaller auxiliary basis and adds an exchange correction.

[

Edit on GitHub

]

Keywords



ADMM_PURIFICATION_METHOD

ADMM_TYPE

BLOCK_LIST

EPS_FILTER

EXCH_CORRECTION_FUNC

EXCH_SCALING_MODEL

METHOD

OPTX_A1

OPTX_A2

OPTX_GAMMA

Keyword descriptions



ADMM_PURIFICATION_METHOD

:

enum

=

MO_DIAG



Valid values:

NONE

Do not apply any purification

CAUCHY

Perform purification via general Cauchy representation

CAUCHY_SUBSPACE

Perform purification via Cauchy representation in occupied subspace

MO_DIAG

Calculate MO derivatives via Cauchy representation by diagonalization

MO_NO_DIAG

Calculate MO derivatives via Cauchy representation by inversion

MCWEENY

Perform original McWeeny purification via matrix multiplications

NONE_DM

Do not apply any purification, works directly with density matrix

Method that shall be used for wavefunction fitting. Use MO_DIAG for MD.

[

Edit on GitHub

]

ADMM_TYPE

:

enum

=

NONE



Valid values:

NONE

No short name is used, use specific definitions (default)

ADMM1

ADMM1 method from Guidon2010

ADMM2

ADMM2 method from Guidon2010

ADMMS

ADMMS method from Merlot2014

ADMMP

ADMMP method from Merlot2014

ADMMQ

ADMMQ method from Merlot2014

References:

Guidon2010

,

Merlot2014

Mentions:

⭐

HFX with ADMM

Named ADMM variant from the literature. This shortcut sets METHOD, ADMM_PURIFICATION_METHOD, and EXCH_SCALING_MODEL consistently for the selected variant.

[

Edit on GitHub

]

BLOCK_LIST

:

integer[

]



Keyword can be repeated.

Usage:

BLOCK_LIST {integer} {integer} .. {integer}

Specifies a list of atoms.

[

Edit on GitHub

]

EPS_FILTER

:

real

=

0.00000000E+000



Usage:

EPS_FILTER

Define accuracy of DBCSR operations

[

Edit on GitHub

]

EXCH_CORRECTION_FUNC

:

enum

=

DEFAULT



Valid values:

DEFAULT

Use PBE-based corrections according to the chosen interaction operator.

PBEX

Use PBEX functional for exchange correction.

NONE

No correction: X(D)-x(d)-> 0.

OPTX

Use OPTX functional for exchange correction.

BECKE88X

Use Becke88X functional for exchange correction.

PBEX_LIBXC

Use PBEX functional (LibXC implementation) for exchange correction.

BECKE88X_LIBXC

Use Becke88X functional (LibXC implementation) for exchange correction.

OPTX_LIBXC

Use OPTX functional (LibXC implementation) for exchange correction.

DEFAULT_LIBXC

Use PBE-based corrections (LibXC where possible) to the chosen interaction operator.

LDA_X_LIBXC

Use Slater X functional (LibXC where possible) for exchange correction.

Mentions:

⭐

HFX with ADMM

Exchange functional used for the ADMM correction. It should be chosen consistently with the exchange functional in the main XC setup. LibXC implementations require linking with LibXC.

[

Edit on GitHub

]

EXCH_SCALING_MODEL

:

enum

=

NONE



Valid values:

NONE

No scaling is enabled, refers to methods ADMM1, ADMM2 or ADMMQ.

MERLOT

Exchange scaling according to Merlot (2014)

Scaling of the exchange correction calculated by the auxiliary density matrix.

[

Edit on GitHub

]

METHOD

:

enum

=

BASIS_PROJECTION



Valid values:

BASIS_PROJECTION

Construct auxiliary density matrix from auxiliary basis.

BLOCKED_PROJECTION_PURIFY_FULL

Construct auxiliary density from a blocked Fock matrix, but use the original matrix for purification.

BLOCKED_PROJECTION

Construct auxiliary density from a blocked Fock matrix.

CHARGE_CONSTRAINED_PROJECTION

Construct auxiliary density from auxiliary basis enforcing charge constrain.

Method that shall be used for wavefunction fitting. Use BASIS_PROJECTION for MD.

[

Edit on GitHub

]

OPTX_A1

:

real

=

1.05151000E+000



OPTX a1 coefficient

[

Edit on GitHub

]

OPTX_A2

:

real

=

1.43169000E+000



OPTX a2 coefficient

[

Edit on GitHub

]

OPTX_GAMMA

:

real

=

6.00000000E-003



OPTX gamma coefficient

[

Edit on GitHub

]
