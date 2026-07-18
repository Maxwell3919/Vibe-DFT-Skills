# CP2K official manual snapshot: wf-correlation

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/WF_CORRELATION.html
- Raw SHA-256: 864fa16348adb1b1736c97314dda8da37071bfd68e5c356c31b4b0395b567f46
- Status: version-matched cached official text; reopen the source for current live verification.

WF_CORRELATION



Section can be repeated.

References:

DelBen2012

,

DelBen2013

,

DelBen2015

,

DelBen2015b

,

Rybkin2016

,

Wilhelm2016

,

Wilhelm2016b

,

Wilhelm2017

,

Wilhelm2018

,

Stein2022

,

Stein2024

,

Bussy2023

Controls wavefunction-based correlation methods such as MP2, RI-MP2, RI-SOS-MP2, RI-RPA, and GW inside RI-RPA.

[

Edit on GitHub

]

Subsections

CANONICAL_GRADIENTS

INTEGRALS

LOW_SCALING

MP2

PRINT

RI

RI_MP2

RI_RPA

RI_SOS_MP2

Keywords



E_GAP

E_RANGE

GROUP_SIZE

MEMORY

SCALE_S

SCALE_T

Keyword descriptions



E_GAP

:

real

=

-1.00000000E+000



Usage:

E_GAP 0.5

Gap energy for integration grids in Hartree. Defaults to -1.0 (automatic determination). Recommended to set if several RPA or SOS-MP2 gradient calculations are requested or to be restarted. In this way, differences of integration grids across different runs are removed as CP2K does not include derivatives thereof.

[

Edit on GitHub

]

E_RANGE

:

real

=

-1.00000000E+000



Usage:

E_RANGE 10.0

Energy range (ratio of largest and smallest) energy difference of unoccupied and occupied orbitals for integration grids. Defaults to 0.0 (automatic determination). Recommended to set if several RPA or SOS-MP2 gradient calculations are requested or to be restarted. In this way, differences of integration grids across different runs are removed as CP2K does not include derivatives thereof.

[

Edit on GitHub

]

GROUP_SIZE

:

integer

=

1



Aliases:

NUMBER_PROC

Usage:

GROUP_SIZE 2

Mentions:

⭐

Random-Phase Approximation and Laplace-Transformed Scaled-Opposite-Spin-MP2

Group size used in the computation of GPW and MME integrals and the MP2 correlation energy. The group size must be a divisor of the total number of MPI ranks. A smaller group size (for example the number of MPI ranks per node) accelerates the computation of integrals but a too large group size increases communication costs. A too small group size may lead to out of memory.

[

Edit on GitHub

]

MEMORY

:

real

=

1.02400000E+003



Usage:

MEMORY 1500

Maximum allowed total memory usage during MP2 and related WF_CORRELATION methods [MiB].

[

Edit on GitHub

]

SCALE_S

:

real

=

1.00000000E+000



Usage:

SCALE_S 1.0

Mentions:

⭐

Møller–Plesset Perturbation Theory

, ⭐

Random-Phase Approximation and Laplace-Transformed Scaled-Opposite-Spin-MP2

Scaling factor of the singlet energy component (opposite spin, OS) of the MP2, RI-MP2 and SOS-MP2 correlation energy.

[

Edit on GitHub

]

SCALE_T

:

real

=

1.00000000E+000



Usage:

SCALE_T 1.0

Mentions:

⭐

Møller–Plesset Perturbation Theory

Scaling factor of the triplet energy component (same spin, SS) of the MP2 and RI-MP2 correlation energy.

[

Edit on GitHub

]
