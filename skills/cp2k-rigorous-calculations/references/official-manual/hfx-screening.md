# CP2K official manual snapshot: hfx-screening

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/SCREENING.html
- Raw SHA-256: 40d9c50f2a0f63a43f4b907280f6bc0eaf970c6ad10371d94fecff2dd2140434
- Status: version-matched cached official text; reopen the source for current live verification.

SCREENING



References:

Guidon2008

,

Guidon2009

Controls screening thresholds for Hartree-Fock exchange integrals.

[

Edit on GitHub

]

Keywords



EPS_SCHWARZ

EPS_SCHWARZ_FORCES

P_SCREEN_CORRECTION_FACTOR

SCREEN_ON_INITIAL_P

SCREEN_P_FORCES

Keyword descriptions



EPS_SCHWARZ

:

real

=

1.00000000E-010



Usage:

EPS_SCHWARZ 1.0E-6

Schwarz inequality threshold for screening near-field electronic repulsion integrals. Tighter values reduce screening error but increase cost.

[

Edit on GitHub

]

EPS_SCHWARZ_FORCES

:

real

=

1.00000000E-006



Usage:

EPS_SCHWARZ_FORCES 1.0E-5

Schwarz threshold used for force-related electronic repulsion integrals. This is approximately the force accuracy and should normally be similar to EPS_SCF. Default value is 100*EPS_SCHWARZ.

[

Edit on GitHub

]

P_SCREEN_CORRECTION_FACTOR

:

real

=

0.00000000E+000



Usage:

P_SCREEN_CORRECTION_FACTOR 0.0_dp

Recalculates integrals on the fly if the actual density matrix is larger by a given factor than the initial one. If the factor is set to 0.0_dp, this feature is disabled.

[

Edit on GitHub

]

SCREEN_ON_INITIAL_P

:

logical

=

F



Usage:

SCREEN_ON_INITIAL_P TRUE

Mentions:

⭐

How to make a SCF run converge

Screen on an initial density matrix. For the first MD step this matrix must be provided by a Restart File.

[

Edit on GitHub

]

SCREEN_P_FORCES

:

logical

=

T



Usage:

SCREEN_P_FORCES TRUE

Screens the electronic repulsion integrals for the forces using the density matrix. Will be disabled for the response part of forces in MP2/RPA/TDDFT. This results in a significant speedup for large systems, but might require a somewhat tigher EPS_SCHWARZ_FORCES.

[

Edit on GitHub

]
