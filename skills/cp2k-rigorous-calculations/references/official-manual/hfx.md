# CP2K official manual snapshot: hfx

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF.html
- Raw SHA-256: 1c5bbbff7aa7d8305e2c92f7a8be3b02825e754c9c0a22cb371de9b2ac3d878e
- Status: version-matched cached official text; reopen the source for current live verification.

HF



Section can be repeated.

References:

Guidon2008

,

Guidon2009

Controls Hartree-Fock exchange for hybrid DFT, Hartree-Fock, and related post-Hartree-Fock workflows.

[

Edit on GitHub

]

Subsections

ACE

HF_INFO

INTERACTION_POTENTIAL

LOAD_BALANCE

MEMORY

PERIODIC

RI

SCREENING

Keywords



FRACTION

HFX_LIBRARY

PW_HFX

PW_HFX_BLOCKSIZE

TREAT_LSD_IN_CORE

Keyword descriptions



FRACTION

:

real

=

1.00000000E+000



Usage:

FRACTION 1.0

Fraction of Hartree-Fock exchange to add to the total energy. 1.0 implies standard Hartree-Fock if used with XC_FUNCTIONAL NONE. NOTE: In a mixed potential calculation this should be set to 1.0, otherwise all parts are multiplied with this factor.

[

Edit on GitHub

]

HFX_LIBRARY

:

enum

=

LIBINT



Usage:

HFX_LIBRARY libGint

Valid values:

LIBINT

libint: use the libint library to compute the 2 electron integrals for HFX/r

LIBGINT

libGint: use the libGint library to accelerate the calculation of the HF exchange on (cuda) GPUs /r

BOTH

both: temporary debug option, will run both libint and libGint and check if the fock matrix is within tolerance

Which library should be used in the calculation of the HF exchange (Libint (cpu, default), libGint(gpu, cuda), both(debug,temporary)

[

Edit on GitHub

]

PW_HFX

:

logical

=

F



Lone keyword:

T

Usage:

PW_HFX FALSE

Compute the Hartree-Fock energy also in the plane wave basis. The value is ignored, and intended for debugging only.

[

Edit on GitHub

]

PW_HFX_BLOCKSIZE

:

integer

=

20



Usage:

PW_HFX_BLOCKSIZE 20

Improve the performance of pw_hfx at the cost of some additional memory by storing the realspace representation of PW_HFX_BLOCKSIZE states.

[

Edit on GitHub

]

TREAT_LSD_IN_CORE

:

logical

=

F



Usage:

TREAT_LSD_IN_CORE TRUE

Determines how spin densities are taken into account. If true, the beta spin density is included via a second in core call. If false, alpha and beta spins are done in one shot

[

Edit on GitHub

]
