# CP2K official manual snapshot: dft-plus-u

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND/DFT_PLUS_U.html
- Raw SHA-256: a4c4ae9012870180fea370d0218d02bdff755e2ba614f79e94855bf7e7b3d5ff
- Status: version-matched cached official text; reopen the source for current live verification.

DFT_PLUS_U



Define the parameters for a DFT+U run

[

Edit on GitHub

]

Subsections

ENFORCE_OCCUPATION

Keywords



SECTION_PARAMETERS

ALPHA

BETA

EPS_U_RAMPING

INIT_U_RAMPING_EACH_SCF

J

J0

L

N

OCCUPATION

U

U_MINUS_J

U_RAMPING

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

&DFT_PLUS_U ON

Controls the activation of the DFT+U section

[

Edit on GitHub

]

ALPHA

:

real

=

0.00000000E+000

[hartree]



Usage:

alpha [eV] 1.4

alpha parameter in the theory of Dudarev et al. Ignored unless pwdft is used

[

Edit on GitHub

]

BETA

:

real

=

0.00000000E+000

[hartree]



Usage:

beta [eV] 1.4

beta parameter in the theory of Dudarev et al. Ignored unless pwdft is used

[

Edit on GitHub

]

EPS_U_RAMPING

:

real

=

1.00000000E-005



Usage:

EPS_U_RAMPING 1.0E-6

Threshold value (SCF convergence) for incrementing the effective U value when U ramping is active.

[

Edit on GitHub

]

INIT_U_RAMPING_EACH_SCF

:

logical

=

F



Lone keyword:

T

Usage:

INIT_U_RAMPING_EACH_SCF on

Set the initial U ramping value to zero before each wavefunction optimisation. The default is to apply U ramping only for the initial wavefunction optimisation.

[

Edit on GitHub

]

J

:

real

=

0.00000000E+000

[hartree]



Usage:

J [eV] 1.4

J parameter in the theory of Dudarev et al. Ignored unless pwdft is used

[

Edit on GitHub

]

J0

:

real

=

0.00000000E+000

[hartree]



Usage:

J0 [eV] 1.4

J0 parameter in the theory of Dudarev et al. Ignored unless pwdft is used

[

Edit on GitHub

]

L

:

integer

=

-1



Usage:

L 2

Angular momentum quantum number of the orbitals to which the correction is applied

[

Edit on GitHub

]

N

:

integer

=

-1



Usage:

N 2

principal quantum number of the orbitals to which the correction is applied. Ignored unless pwdft is used for the calculations

[

Edit on GitHub

]

OCCUPATION

:

real

=

0.00000000E+000



Usage:

occupation 6

number of electrons in the hubbard shell. Ignored unless pwdft is used

[

Edit on GitHub

]

U

:

real

=

0.00000000E+000

[hartree]



Usage:

U [eV] 1.4

U parameter in the theory of Dudarev et al. Ignored unless pwdft is used

[

Edit on GitHub

]

U_MINUS_J

:

real

=

0.00000000E+000

[hartree]



Aliases:

U_EFF

Usage:

U_MINUS_J [eV] 1.4

Effective parameter U(eff) = U - J

[

Edit on GitHub

]

U_RAMPING

:

real

=

0.00000000E+000

[hartree]



Usage:

U_RAMPING [eV] 0.1

Increase the effective U parameter stepwise using the specified increment until the target value given by U_MINUS_J is reached.

[

Edit on GitHub

]
