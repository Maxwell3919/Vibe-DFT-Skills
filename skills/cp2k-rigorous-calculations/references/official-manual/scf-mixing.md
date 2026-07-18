# CP2K official manual snapshot: scf-mixing

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/MIXING.html
- Raw SHA-256: 18b2772c8d76564fa4ace05fa597455a3643cfaabd80ed972543012b793ac3f0
- Status: version-matched cached official text; reopen the source for current live verification.

MIXING



Define type and parameters for mixing procedures to be applied to the density matrix. Normally, only one type of mixing method should be accepted. The mixing procedures activated by this section are only active for diagonalization methods and linear scaling SCF, i.e. not with minimization methods based on OT.

[

Edit on GitHub

]

Keywords



SECTION_PARAMETERS

ALPHA

ALPHA_MAG

BETA

BETA_MAG

BROY_W0

BROY_WMAX

BROY_WREF

GMIX_P

MAX_GVEC_EXP

MAX_STEP

METHOD

NBUFFER

NMIXING

NSKIP

N_SIMPLE_MIX

PULAY_ALPHA

PULAY_BETA

QK

QKAPPA

QM

REGULARIZATION

R_FACTOR

Keyword descriptions



SECTION_PARAMETERS

:

logical

=

T



Lone keyword:

T

Usage:

&MIXING ON

Controls the activation of the mixing procedure

[

Edit on GitHub

]

ALPHA

:

real

=

4.00000000E-001



Usage:

ALPHA 0.2

Fraction of new density to be included

[

Edit on GitHub

]

ALPHA_MAG

:

real

=

-1.00000000E+000



Usage:

ALPHA_MAG 0.8

Fraction of new magnetization density to be included (for spin-polarized calculations, ispin=2 channel after rho_total/m transform). A negative value (default) means: use the same value as ALPHA. For magnetic transition-metal systems, a larger value (e.g. 0.8-1.6) than ALPHA often improves convergence.

[

Edit on GitHub

]

BETA

:

real

=

5.00000000E-001

[bohr^-1]



Usage:

BETA 1.5

Denominator parameter in Kerker damping introduced to suppress charge sloshing: rho_mix(g) = rho_in(g) + alpha

g^2/(g^2 + beta^2)

(rho_out(g)-rho_in(g))

[

Edit on GitHub

]

BETA_MAG

:

real

=

-1.00000000E+000

[bohr^-1]



Usage:

BETA_MAG 0.0

Kerker damping parameter for the magnetization channel (for spin-polarized calculations). A negative value (default) means: use the same value as BETA. Set to 0.0 to disable Kerker screening on the magnetization density, which avoids suppression of long-range magnetic order formation in transition-metal systems.

[

Edit on GitHub

]

BROY_W0

:

real

=

1.00000000E-002



Usage:

BROY_W0 0.03

Regularization weight used in Broyden mixing. For the original BROYDEN_MIXING method this is the constant diagonal regularization of the small Broyden system. For MODIFIED_BROYDEN_MIXING it is the corresponding diagonal regularization of the dynamically weighted Broyden system. The default follows tblite.

[

Edit on GitHub

]

BROY_WMAX

:

real

=

1.00000000E+005



Usage:

BROY_WMAX 100000.0

Upper bound for the dynamic residual weight. This keyword is only used by MODIFIED_BROYDEN_MIXING; the original BROYDEN_MIXING path is unchanged. The lower bound is fixed to 1.0. The default follows tblite.

[

Edit on GitHub

]

BROY_WREF

:

real

=

1.00000000E-002



Usage:

BROY_WREF 0.01

Reference factor for the dynamic residual weight. This keyword is only used by MODIFIED_BROYDEN_MIXING; the original BROYDEN_MIXING path is unchanged. The effective history weight is proportional to BROY_WREF divided by the residual norm, clipped to the interval [1, BROY_WMAX]. The default follows tblite.

[

Edit on GitHub

]

GMIX_P

:

logical

=

F



Lone keyword:

T

Usage:

GMIX_P

Activate the mixing of the density matrix, using the same mixing coefficient applied for the g-space mixing.

[

Edit on GitHub

]

MAX_GVEC_EXP

:

real

=

-1.00000000E+000



Usage:

MAX_GVEC_EXP 3.

Restricts the G-space mixing to lower part of G-vector spectrum, up to a G0, by assigning the exponent of the Gaussian that can be represented by vectors smaller than G0 within a certain accuracy.

[

Edit on GitHub

]

MAX_STEP

:

real

=

1.00000000E-001



Usage:

MAX_STEP .2

Upper bound for the magnitude of the unpredicted step size in the update by the multisecant mixing scheme

[

Edit on GitHub

]

METHOD

:

enum

=

DIRECT_P_MIXING



Usage:

METHOD KERKER_MIXING

Valid values:

NONE

No mixing is applied

DIRECT_P_MIXING

Direct mixing of new and old density matrices

KERKER_MIXING

Mixing of the potential in reciprocal space using the Kerker damping

PULAY_MIXING

Pulay mixing

BROYDEN_MIXING

Original CP2K Broyden mixing with a constant BROY_W0 regularization

MODIFIED_BROYDEN_MIXING

Modified Broyden mixing with dynamic residual weights controlled by BROY_W0, BROY_WREF, and BROY_WMAX

MULTISECANT_MIXING

Multisecant scheme for mixing

NEW_PULAY_MIXING

New Pulay mixing using Sundararaman et al.’s metric and preconditioner, with improved convergence behavior and suitable for grand canonical SCF

Mentions:

⭐

How to make a SCF run converge

Mixing method to be applied

[

Edit on GitHub

]

NBUFFER

:

integer

=

4



Aliases:

NPULAY ,NBROYDEN ,NMULTISECANT

Usage:

NBUFFER 2

Number of previous steps stored for the actual mixing scheme

[

Edit on GitHub

]

NMIXING

:

integer

=

2



Usage:

NMIXING 1

Minimal number of density mixing (should be greater than 0), before starting DIIS

[

Edit on GitHub

]

NSKIP

:

integer

=

0



Aliases:

NSKIP_MIXING

Usage:

NSKIP 10

Number of initial iteration for which the mixing is skipped

[

Edit on GitHub

]

N_SIMPLE_MIX

:

integer

=

0



Aliases:

NSIMPLEMIX

Usage:

NSIMPLEMIX

Number of kerker damping iterations before starting other mixing procedures

[

Edit on GitHub

]

PULAY_ALPHA

:

real

=

0.00000000E+000



Usage:

PULAY_ALPHA 0.2

Fraction of new density to be added to the Pulay expansion

[

Edit on GitHub

]

PULAY_BETA

:

real

=

1.00000000E+000



Usage:

PULAY_BETA 0.2

Fraction of residual contribution to be added to Pulay expansion

[

Edit on GitHub

]

QK

:

real

=

3.00000000E+000

[bohr^-1]



Usage:

QK 3.0

The control parameter in the denominator of the Kerker preconditioner used in the new Pulay mixing, introduced to suppress charge sloshing: Kerker preconditioner: K(g) = alpha * (g^2 + qkapa^2)/(g^2 + qk^2 + qkapa^2)

[

Edit on GitHub

]

QKAPPA

:

real

=

2.50000000E-001

[bohr^-1]



Usage:

QKAPPA 0.25

The control parameter in the numerator and the denominator of the Pulay metric and the Kerker preconditioner used in the new Pulay mixing, introduced to ensure a finite and well-defined Pulay metric at g=0 and a non-zero and well-defined Kerker preconditioner at g=0

[

Edit on GitHub

]

QM

:

real

=

7.50000000E-001

[bohr^-1]



Usage:

QM 0.75

The control parameter in the numerator of the Pulay metric used in the new Pulay mixing, introduced to suppress charge sloshing: Pulay metric: M(g) = (g^2 + qm^2 + qkapa^2)/(g^2 + qkapa^2)

[

Edit on GitHub

]

REGULARIZATION

:

real

=

1.00000000E-005



Usage:

REGULARIZATION 0.000001

Regularization parameter to stabilize the inversion of the residual matrix {Yn^t Yn} in the multisecant mixing scheme (noise)

[

Edit on GitHub

]

R_FACTOR

:

real

=

5.00000000E-002



Usage:

R_FACTOR .12

Control factor for the magnitude of the unpredicted step size in the update by the multisecant mixing scheme

[

Edit on GitHub

]
