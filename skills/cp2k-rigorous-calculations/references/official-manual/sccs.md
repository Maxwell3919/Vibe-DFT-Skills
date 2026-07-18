# CP2K official manual snapshot: sccs

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCCS.html
- Raw SHA-256: 44d4e91caee4e40ab46396d57544f0a25f80c9e75232da73f17191a55ccf5c6b
- Status: version-matched cached official text; reopen the source for current live verification.

SCCS



References:

Fattebert2002

,

Andreussi2012

,

Yin2017

Define the parameters for self-consistent continuum solvation (SCCS) model

[

Edit on GitHub

]

Subsections

ANDREUSSI

FATTEBERT-GYGI

SAA_ANDREUSSI

Keywords



SECTION_PARAMETERS

ALPHA

BETA

DELTA_RHO

DERIVATIVE_METHOD

EPS_SCCS

EPS_SCF

GAMMA

MAX_ITER

METHOD

MIXING

RELATIVE_PERMITTIVITY

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

&SCCS ON

Controls the activation of the SCCS section

[

Edit on GitHub

]

ALPHA

:

real

=

0.00000000E+000

[mN*m^-1]



Solvent specific tunable parameter for the calculation of the repulsion term

\(G^\text{rep} = \alpha S\)

where

\(S\)

is the (quantum) surface of the cavity

[

Edit on GitHub

]

BETA

:

real

=

0.00000000E+000

[GPa]



Solvent specific tunable parameter for the calculation of the dispersion term

\(G^\text{dis} = \beta V\)

where

\(V\)

is the (quantum) volume of the cavity

[

Edit on GitHub

]

DELTA_RHO

:

real

=

2.00000000E-005



Numerical increment for the calculation of the (quantum) surface of the solute cavity

[

Edit on GitHub

]

DERIVATIVE_METHOD

:

enum

=

FFT



Usage:

DERIVATIVE_METHOD cd5

Valid values:

FFT

Fast Fourier transformation

CD3

3-point stencil central differences

CD5

5-point stencil central differences

CD7

7-point stencil central differences

Method for the calculation of the numerical derivatives on the real-space grids

[

Edit on GitHub

]

EPS_SCCS

:

real

=

1.00000000E-006



Aliases:

EPS_ITER ,TAU_POL

Usage:

EPS_ITER 1.0E-7

Tolerance for the convergence of the polarisation density, i.e. requested accuracy for the SCCS iteration cycle

[

Edit on GitHub

]

EPS_SCF

:

real

=

5.00000000E-001



Usage:

EPS_SCF 1.0E-2

The SCCS iteration cycle is activated only if the SCF iteration cycle is converged to this threshold value

[

Edit on GitHub

]

GAMMA

:

real

=

0.00000000E+000

[mN*m^-1]



Aliases:

SURFACE_TENSION

Surface tension of the solvent used for the calculation of the cavitation term

\(G^\text{cav} = \gamma S\)

where

\(S\)

is the (quantum) surface of the cavity

[

Edit on GitHub

]

MAX_ITER

:

integer

=

100



Usage:

MAX_ITER 50

Maximum number of SCCS iteration steps performed to converge within the given tolerance

[

Edit on GitHub

]

METHOD

:

enum

=

ANDREUSSI



Usage:

METHOD Fattebert-Gygi

Valid values:

ANDREUSSI

Smoothing function proposed by Andreussi et al.

FATTEBERT-GYGI

Smoothing function proposed by Fattebert and Gygi

SAA_ANDREUSSI

Smoothing function of the solvent aware algorithm

Method used for the smoothing of the dielectric function

[

Edit on GitHub

]

MIXING

:

real

=

6.00000000E-001



Aliases:

ETA

Usage:

MIXING 0.2

Mixing parameter (Hartree damping) employed during the iteration procedure

[

Edit on GitHub

]

RELATIVE_PERMITTIVITY

:

real

=

8.00000000E+001



Aliases:

DIELECTRIC_CONSTANT ,EPSILON_RELATIVE ,EPSILON_SOLVENT

Usage:

RELATIVE_PERMITTIVITY 78.36

Relative permittivity (dielectric constant) of the solvent (medium)

[

Edit on GitHub

]
