# CP2K official manual snapshot: real-time-propagation

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/REAL_TIME_PROPAGATION.html
- Raw SHA-256: 19c42ffd401ce0de2b765f95124eaf86fd5cf18b5be75a777b9362c54aca2a32
- Status: version-matched cached official text; reopen the source for current live verification.

REAL_TIME_PROPAGATION



References:

Kunert2003

,

Andermatt2016

Parameters needed to set up the real time propagation for the electron dynamics. This currently works only in the NVE ensemble.

[

Edit on GitHub

]

Subsections

FT

PRINT

RTBSE

Keywords



ACCURACY_REFINEMENT

APPLY_DELTA_PULSE

APPLY_DELTA_PULSE_MAG

APPLY_WFN_MIX_INIT_RESTART

ASPC_ORDER

COM_NL

DELTA_PULSE_DIRECTION

DELTA_PULSE_SCALE

DENSITY_PROPAGATION

EPS_ITER

EXP_ACCURACY

GAUGE_ORIG

GAUGE_ORIG_MANUAL

HFX_BALANCE_IN_CORE

INITIAL_WFN

LEN_REP

LOCALIZE

MAT_EXP

MAX_ITER

MCWEENY_EPS

MCWEENY_MAX_ITER

PERIODIC

PROPAGATOR

SC_CHECK_START

VELOCITY_GAUGE

VG_COM_NL

Keyword descriptions



ACCURACY_REFINEMENT

:

integer

=

100



Usage:

ACCURACY_REFINEMENT

If using density propagation some parts should be calculated with a higher accuracy than the rest to reduce numerical noise. This factor determines by how much the filtering threshold is reduced for these calculations.

[

Edit on GitHub

]

APPLY_DELTA_PULSE

:

logical

=

F



Lone keyword:

T

Usage:

APPLY_DELTA_PULSE

Mentions:

⭐

Real-Time Bethe-Salpeter Propagation

Applies a delta kick to the initial wfn (only RTP for now - the EMD case is not yet implemented). Only work for INITIAL_WFN=SCF_WFN

[

Edit on GitHub

]

APPLY_DELTA_PULSE_MAG

:

logical

=

F



Lone keyword:

T

Usage:

APPLY_DELTA_PULSE_MAG

Applies a magnetic delta kick to the initial wfn (only RTP for now - the EMD case is not yet implemented). Only work for INITIAL_WFN=SCF_WFN

[

Edit on GitHub

]

APPLY_WFN_MIX_INIT_RESTART

:

logical

=

F



Lone keyword:

T

Usage:

APPLY_WFN_MIX_INIT_RESTART

If set to True and in the case of INITIAL_WFN=RESTART_WFN, call the DFT%PRINT%WFN_MIX section to mix the read initial wfn. The starting wave-function of the RTP will be the mixed one. Setting this to True without a defined WFN_MIX section will not do anything as defining a WFN_MIX section without this keyword for RTP run with INITIAL_WFN=RESTART_WFN. Note that if INITIAL_WFN=SCF_WFN, this keyword is not needed to apply the mixing defined in the WFN_MIX section. Default is False.

[

Edit on GitHub

]

ASPC_ORDER

:

integer

=

3



Usage:

ASPC_ORDER 3

Speciefies how many steps will be used for extrapolation. One will be always used which is means X(t+dt)=X(t)

[

Edit on GitHub

]

COM_NL

:

logical

=

T



Lone keyword:

T

Usage:

COM_NL

Include non-local commutator for periodic delta pulse. only affects PERIODIC=.TRUE.

[

Edit on GitHub

]

DELTA_PULSE_DIRECTION

:

integer

[

3

]

=

1

0



Usage:

DELTA_PULSE_DIRECTION 1 1 1

Mentions:

⭐

Real-Time Bethe-Salpeter Propagation

, ⭐

X-Ray Absorption from RTP and \delta-Kick perturbation

Direction of the applied electric field. The k vector is given as 2

Pi

[i,j,k]

inv(h_mat), which for PERIODIC .FALSE. yields exp(ikr) periodic with the unit cell, only if DELTA_PULSE_SCALE is set to unity. For an orthorhombic cell [1,0,0] yields [2

Pi/L_x,0,0]. For small cells, this results in a very large kick.

[

Edit on GitHub

]

DELTA_PULSE_SCALE

:

real

=

1.00000000E-003



Usage:

DELTA_PULSE_SCALE 0.01

Mentions:

⭐

Real-Time Bethe-Salpeter Propagation

, ⭐

X-Ray Absorption from RTP and \delta-Kick perturbation

Scale the k vector, which for PERIODIC .FALSE. results in exp(ikr) no longer being periodic with the unit cell. The norm of k is the strength of the applied electric field in atomic units.

[

Edit on GitHub

]

DENSITY_PROPAGATION

:

logical

=

F



Lone keyword:

T

Usage:

DENSITY_PROPAGATION .TRUE.

Mentions:

⭐

Real-Time Propagation and Ehrenfest MD

The density matrix is propagated instead of the molecular orbitals. This can allow a linear scaling simulation. The density matrix is filtered with the threshold based on the EPS_FILTER keyword from the LS_SCF section

[

Edit on GitHub

]

EPS_ITER

:

real

=

1.00000000E-007



Usage:

EPS_ITER 1.0E-5

Mentions:

⭐

Real-Time Bethe-Salpeter Propagation

, ⭐

Real-Time Propagation and Ehrenfest MD

Convergence criterion for the self consistent propagator loop.

[

Edit on GitHub

]

EXP_ACCURACY

:

real

=

1.00000000E-009



Usage:

EXP_ACCURACY 1.0E-6

Mentions:

⭐

Real-Time Bethe-Salpeter Propagation

Accuracy for the taylor and pade approximation. This is only an upper bound bound since the norm used for the guess is an upper bound for the needed one.

[

Edit on GitHub

]

GAUGE_ORIG

:

enum

=

COM



Usage:

GAUGE_ORIG COM

Valid values:

COM

Use Center of Mass

COAC

Use Center of Atomic Charges

USER_DEFINED

Use User Defined Point (Keyword:REF_POINT)

ZERO

Use Origin of Coordinate System

Define gauge origin for magnetic perturbation

[

Edit on GitHub

]

GAUGE_ORIG_MANUAL

:

real

[

3

]

=

0.00000000E+000

[bohr]



Usage:

GAUGE_ORIG_MANUAL x y z

Manually defined gauge origin for magnetic perturbation [in Bohr!]

[

Edit on GitHub

]

HFX_BALANCE_IN_CORE

:

logical

=

F



Lone keyword:

T

Usage:

HFX_BALANCE_IN_CORE

If HFX is used, this keyword forces a redistribution/recalculation of the integrals, balanced with respect to the in core steps.

[

Edit on GitHub

]

INITIAL_WFN

:

enum

=

SCF_WFN



Usage:

INITIAL_WFN SCF_WFN

Valid values:

SCF_WFN

An SCF run is performed to get the initial state.

RESTART_WFN

A wavefunction from a previous SCF is propagated. Especially useful, if electronic constraints or restraints are used in the previous calculation, since these do not work in the rtp scheme.

RT_RESTART

use the wavefunction of a real time propagation/ehrenfest run

Mentions:

⭐

Real-Time Propagation and Ehrenfest MD

Controls the initial WFN used for propagation. Note that some energy contributions may not be initialized in the restart cases, for instance electronic entropy energy in the case of smearing.

[

Edit on GitHub

]

LEN_REP

:

logical

=

F



Lone keyword:

T

Usage:

LEN_REP T

Use length representation delta pulse (in conjunction with PERIODIC T). This corresponds to a 1st order perturbation in the length gauge. Note that this is NOT compatible with a periodic calculation! Uses the reference point defined in DFT%PRINT%MOMENTS

[

Edit on GitHub

]

LOCALIZE

:

integer

=

0



Usage:

LOCALIZE

Localise the Molecular orbitals each n steps real-time propagated TDDFT, 0 means never localise

[

Edit on GitHub

]

MAT_EXP

:

enum

=

ARNOLDI



Usage:

MAT_EXP TAYLOR

Valid values:

TAYLOR

exponential is evaluated using scaling and squaring in combination with a taylor expansion of the exponential.

PADE

uses scaling and squaring together with the pade approximation

ARNOLDI

uses arnoldi subspace algorithm to compute exp(H)*MO directly, can’t be used in combination with Crank Nicholson or density propagation

BCH

Uses a Baker-Campbell-Hausdorff expansion to propagate the density matrix, only works for density propagation

EXACT

Uses diagonalisation of the exponent matrices to determine the matrix exponential exactly. Only implemented for GWBSE.

Mentions:

⭐

Real-Time Bethe-Salpeter Propagation

, ⭐

Real-Time Propagation and Ehrenfest MD

Which method should be used to calculate the exponential in the propagator. It is recommended to use BCH when employing density_propagation and ARNOLDI otherwise.

[

Edit on GitHub

]

MAX_ITER

:

integer

=

10



Usage:

MAX_ITER 10

Mentions:

⭐

Real-Time Bethe-Salpeter Propagation

, ⭐

Real-Time Propagation and Ehrenfest MD

Maximal number of iterations for the self consistent propagator loop.

[

Edit on GitHub

]

MCWEENY_EPS

:

real

=

0.00000000E+000



Usage:

MCWEENY_EPS 0.00001

Threshold after which McWeeny is terminated

[

Edit on GitHub

]

MCWEENY_MAX_ITER

:

integer

=

1



Usage:

MCWEENY_MAX_ITER 2

Determines the maximum amount of McWeeny steps used after each converged step in density propagation

[

Edit on GitHub

]

PERIODIC

:

logical

=

T



Lone keyword:

T

Usage:

PERIODIC

Mentions:

⭐

X-Ray Absorption from RTP and \delta-Kick perturbation

Apply a delta-kick that is compatible with periodic boundary conditions for any value of DELTA_PULSE_SCALE. Uses perturbation theory for the preparation of the initial wfn with the velocity operator as perturbation. If LEN_REP is .FALSE. this corresponds to a first order velocity gauge. Note that the pulse is only applied when INITIAL_WFN is set to SCF_WFN, and not for restarts (RT_RESTART).

[

Edit on GitHub

]

PROPAGATOR

:

enum

=

ETRS



Usage:

PROPAGATOR ETRS

Valid values:

ETRS

enforced time reversible symmetry

CN

Crank Nicholson propagator

EM

Exponential midpoint propagator

Which propagator should be used for the orbitals

[

Edit on GitHub

]

SC_CHECK_START

:

integer

=

0



Usage:

SC_CHECK_START 3

Speciefies how many iteration steps will be done without a check for self consistency. Can save some time in big calculations.

[

Edit on GitHub

]

VELOCITY_GAUGE

:

logical

=

F



Lone keyword:

T

Usage:

VELOCITY_GAUGE T

Perform propagation in the velocity gauge using the explicit vector potential only a constant vector potential as of now (corresonding to a delta-pulse). uses DELTA_PULSE_SCALE and DELTA_PULSE_DIRECTION to define the vector potential

[

Edit on GitHub

]

VG_COM_NL

:

logical

=

T



Lone keyword:

T

Usage:

VG_COM_NL T

apply gauge transformed non-local potential term only affects VELOCITY_GAUGE=.TRUE.

[

Edit on GitHub

]
