# CP2K official manual snapshot: xc

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC.html
- Raw SHA-256: 6dd62cbe5e1a2ec40ee81f90c55c2811f005999cea906d3f9b72c4bbba486d47
- Status: version-matched cached official text; reopen the source for current live verification.

XC



Parameters needed for the calculation of the eXchange and Correlation potential

[

Edit on GitHub

]

Subsections

ADIABATIC_RESCALING

GCP_POTENTIAL

HF

HFX_KERNEL

VDW_POTENTIAL

WF_CORRELATION

XC_FUNCTIONAL

XC_GRID

XC_KERNEL

XC_POTENTIAL

Keywords



2ND_DERIV_ANALYTICAL

3RD_DERIV_ANALYTICAL

DENSITY_CUTOFF

DENSITY_SMOOTH_CUTOFF_RANGE

GRADIENT_CUTOFF

NSTEPS

STEP_SIZE

TAU_CUTOFF

Keyword descriptions



2ND_DERIV_ANALYTICAL

:

logical

=

T



Lone keyword:

T

Usage:

2ND_DERIV_ANALYTICAL logical

Use analytical formulas or finite differences for 2nd derivatives of XC

[

Edit on GitHub

]

3RD_DERIV_ANALYTICAL

:

logical

=

T



Lone keyword:

T

Usage:

3RD_DERIV_ANALYTICAL logical

Use analytical formulas or finite differences for 3rd derivatives of XC

[

Edit on GitHub

]

DENSITY_CUTOFF

:

real

=

1.00000000E-010



Usage:

density_cutoff 1.e-11

The cutoff on the density used by the xc calculation

[

Edit on GitHub

]

DENSITY_SMOOTH_CUTOFF_RANGE

:

real

=

0.00000000E+000



Usage:

DENSITY_SMOOTH_CUTOFF_RANGE {real}

Parameter for the smoothing procedure in xc calculation

[

Edit on GitHub

]

GRADIENT_CUTOFF

:

real

=

1.00000000E-010



Usage:

gradient_cutoff 1.e-11

The cutoff on the gradient of the density used by the xc calculation

[

Edit on GitHub

]

NSTEPS

:

integer

=

3



Usage:

NSTEPS 4

Number of steps to consider in each direction for the numerical evaluation of XC derivatives. Must be a value from 1 to 4 (Default: 3).

[

Edit on GitHub

]

STEP_SIZE

:

real

=

1.00000000E-003



Usage:

STEP_SIZE 1.0E-3

Step size in terms of the first order potential for the numerical evaluation of XC derivatives

[

Edit on GitHub

]

TAU_CUTOFF

:

real

=

1.00000000E-010



Usage:

tau_cutoff 1.e-11

The cutoff on tau used by the xc calculation

[

Edit on GitHub

]
