# CP2K official manual snapshot: qs

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/QS.html
- Raw SHA-256: 94d335636fd90dd85be5360505eb6cd126f4435236d05a62381a53682b1da346
- Status: version-matched cached official text; reopen the source for current live verification.

QS



parameters needed to set up the Quickstep framework

[

Edit on GitHub

]

Subsections

CDFT

DDAPC_RESTRAINT

DFTB

DISTRIBUTION

LRIGPW

MULLIKEN_RESTRAINT

OPTIMIZE_LRI_BASIS

OPT_DMFET

OPT_EMBED

S2_RESTRAINT

SE

XTB

Keywords



ALMO_SCF

ALPHA0_HARD

ALPHA_WEIGHTS

CLUSTER_EMBED_SUBSYS

CORE_PPL

DFET_EMBEDDED

DMFET_EMBEDDED

EMBED_CUBE_FILE_NAME

EMBED_RESTART_FILE_NAME

EMBED_SPIN_CUBE_FILE_NAME

EPSFIT

EPSISO

EPSRHO0

EPSSVD

EPS_CORE_CHARGE

EPS_CPC

EPS_DEFAULT

EPS_FILTER_MATRIX

EPS_GVG_RSPACE

EPS_KG_ORB

EPS_PGF_ORB

EPS_PPL

EPS_PPNL

EPS_RHO

EPS_RHO_GSPACE

EPS_RHO_RSPACE

EXTRAPOLATION

EXTRAPOLATION_ORDER

FORCE_PAW

GAPW_1C_BASIS

GAPW_ACCURATE_XCINT

HIGH_LEVEL_EMBED_SUBSYS

KG_METHOD

LADDN0

LMAXN0

LMAXN1

LS_SCF

MAX_RAD_LOCAL

METHOD

MIN_PAIR_LIST_RADIUS

PW_GRID

PW_GRID_BLOCKED

PW_GRID_LAYOUT

QUADRATURE

REF_EMBED_SUBSYS

STO_NG

TRANSPORT

Keyword descriptions



ALMO_SCF

:

logical

=

F



Lone keyword:

T

Usage:

ALMO_SCF

Perform ALMO SCF

[

Edit on GitHub

]

ALPHA0_HARD

:

real

=

0.00000000E+000



Aliases:

ALPHA0_H ,ALPHA0

Usage:

ALPHA0_HARD real

GAPW: Exponent for hard compensation charge

[

Edit on GitHub

]

ALPHA_WEIGHTS

:

real

=

6.00000000E+000



Usage:

ALPHA_WEIGHTS 10.0

Gaussian exponent reference (rc=1.2 Bohr) for accurate integration in GAPW.

[

Edit on GitHub

]

CLUSTER_EMBED_SUBSYS

:

logical

=

F



Lone keyword:

T

Usage:

CLUSTER_EMBED_SUBSYS FALSE

A cluster treated with DFT in DFT embedding.

[

Edit on GitHub

]

CORE_PPL

:

enum

=

ANALYTIC



Usage:

CORE_PPL ANALYTIC

Valid values:

ANALYTIC

Analytic integration of integrals

GRID

Numerical integration on real space grid. Lumped together with core charge

Specifies the method used to calculate the local pseudopotential contribution.

[

Edit on GitHub

]

DFET_EMBEDDED

:

logical

=

F



Lone keyword:

T

Usage:

DFET_EMBEDDED FALSE

Calculation with DFT-embedding potential.

[

Edit on GitHub

]

DMFET_EMBEDDED

:

logical

=

F



Lone keyword:

T

Usage:

DMFET_EMBEDDED FALSE

Calculation with DM embedding potential.

[

Edit on GitHub

]

EMBED_CUBE_FILE_NAME

:

string



Usage:

EMBED_CUBE_FILE_NAME

Root of the file name where to read the embedding potential (guess) as a cube. Whitespace-separated cube values are accepted. If adjacent values are written without whitespace, each value must occupy a 13-character E13.5 field, as in CP2K-generated cube files.

[

Edit on GitHub

]

EMBED_RESTART_FILE_NAME

:

string



Usage:

EMBED_RESTART_FILE_NAME

Root of the file name where to read the embedding potential guess.

[

Edit on GitHub

]

EMBED_SPIN_CUBE_FILE_NAME

:

string



Usage:

EMBED_SPIN_CUBE_FILE_NAME

Root of the file name where to read the spin part of the embedding potential (guess) as a cube. Whitespace-separated cube values are accepted. If adjacent values are written without whitespace, each value must occupy a 13-character E13.5 field, as in CP2K-generated cube files.

[

Edit on GitHub

]

EPSFIT

:

real

=

1.00000000E-004



Aliases:

EPS_FIT

Usage:

EPSFIT real

Mentions:

⭐

Gaussian Augmented Plane Waves

GAPW: tolerance controlling the split of Gaussian basis functions into hard atom-centered and soft grid-expanded parts. Smaller values include harder Gaussians in the soft density and can require a larger MGRID cutoff.

[

Edit on GitHub

]

EPSISO

:

real

=

1.00000000E-012



Aliases:

EPS_ISO

Usage:

EPSISO real

GAPW: precision to determine an isolated projector

[

Edit on GitHub

]

EPSRHO0

:

real

=

1.00000000E-006



Aliases:

EPSVRHO0 ,EPS_VRHO0

Usage:

EPSRHO0 real

Mentions:

⭐

Gaussian Augmented Plane Waves

GAPW: tolerance used to determine the range of the V(rho0-rho0_soft) compensation contribution.

[

Edit on GitHub

]

EPSSVD

:

real

=

1.00000000E-008



Aliases:

EPS_SVD

Usage:

EPS_SVD real

Mentions:

⭐

Gaussian Augmented Plane Waves

GAPW: tolerance used in the singular value decomposition of the projector matrix. Smaller values can improve numerical accuracy at increased cost.

[

Edit on GitHub

]

EPS_CORE_CHARGE

:

real



Usage:

EPS_CORE_CHARGE real

Precision for mapping the core charges.Overrides EPS_DEFAULT/100.0 value

[

Edit on GitHub

]

EPS_CPC

:

real



Usage:

EPS_CPC real

Sets precision of the GAPW projection. Overrides EPS_DEFAULT value

[

Edit on GitHub

]

EPS_DEFAULT

:

real

=

1.00000000E-010



Usage:

EPS_DEFAULT real

Mentions:

⭐

How to make a SCF run converge

, ⭐

Geometry and cell optimization

, ⭐

Molecular Dynamics

Try setting all EPS_xxx to values leading to an energy correct up to EPS_DEFAULT

[

Edit on GitHub

]

EPS_FILTER_MATRIX

:

real

=

0.00000000E+000



Usage:

EPS_FILTER_MATRIX 1.0E-6

Sets the threshold for filtering matrix elements.

[

Edit on GitHub

]

EPS_GVG_RSPACE

:

real



Aliases:

EPS_GVG

Usage:

EPS_GVG_RSPACE real

Sets precision of the realspace KS matrix element integration. Overrides SQRT(EPS_DEFAULT) value

[

Edit on GitHub

]

EPS_KG_ORB

:

real



Usage:

EPS_KG_ORB 1.0E-8

Sets precision used in coloring the subsets for the Kim-Gordon method. Overrides SQRT(EPS_DEFAULT) value

[

Edit on GitHub

]

EPS_PGF_ORB

:

real



Usage:

EPS_PGF_ORB real

Sets precision of the overlap matrix elements. Overrides SQRT(EPS_DEFAULT) value

[

Edit on GitHub

]

EPS_PPL

:

real

=

1.00000000E-002



Usage:

EPS_PPL real

Adjusts the precision for the local part of the pseudo potential.

[

Edit on GitHub

]

EPS_PPNL

:

real



Usage:

EPS_PPNL real

Sets precision of the non-local part of the pseudo potential. Overrides sqrt(EPS_DEFAULT) value

[

Edit on GitHub

]

EPS_RHO

:

real



Usage:

EPS_RHO real

Sets precision of the density mapping on the grids.Overrides EPS_DEFAULT value

[

Edit on GitHub

]

EPS_RHO_GSPACE

:

real



Usage:

EPS_RHO_GSPACE real

Sets precision of the density mapping in gspace.Overrides EPS_DEFAULT value. Overrides EPS_RHO value

[

Edit on GitHub

]

EPS_RHO_RSPACE

:

real



Usage:

EPS_RHO_RSPACE real

Sets precision of the density mapping in rspace.Overrides EPS_DEFAULT value. Overrides EPS_RHO value

[

Edit on GitHub

]

EXTRAPOLATION

:

enum

=

ASPC



Aliases:

INTERPOLATION ,WF_INTERPOLATION

Usage:

EXTRAPOLATION PS

Valid values:

USE_GUESS

Use the method specified with SCF_GUESS, i.e. no extrapolation

USE_PREV_P

Use the previous density matrix

USE_PREV_RHO_R

Legacy alias for USE_PREV_P, using the previous density matrix; deprecated

LINEAR_WF

Linear extrapolation of the wavefunction (not available for k-points)

LINEAR_P

Linear extrapolation of the density matrix

LINEAR_PS

Linear extrapolation of the density matrix times the overlap matrix (not available for k-points)

USE_PREV_WF

Use the previous wavefunction

PS

Higher order extrapolation of the density matrix times the overlap matrix

FROZEN

Frozen … (not available for k-points)

ASPC

Always stable predictor corrector, similar to PS, but going for MD stability instead of initial guess accuracy.

GEXT_PROJ

GExt extrapolation for the density matrix times the overlap matrix.

GEXT_PROJ_QTR

Quasi time reversible GExt extrapolation for the density matrix times the overlap matrix.

References:

Kolafa2004

,

VandeVondele2005

,

Kühne2007

Mentions:

⭐

How to make a SCF run converge

, ⭐

Geometry and cell optimization

, ⭐

Molecular Dynamics

Extrapolation strategy for the wavefunction during e.g. MD. Not all options are available for all simulation methods. PS and ASPC are recommended, see also EXTRAPOLATION_ORDER.

[

Edit on GitHub

]

EXTRAPOLATION_ORDER

:

integer

=

3



Usage:

EXTRAPOLATION_ORDER {integer}

Mentions:

⭐

Geometry and cell optimization

, ⭐

Molecular Dynamics

Order for the PS, ASPC extrapolation (typically 2-4) or order for the GEXT_PROJ, GEXT_PROJ_QTR extrapolation (typically 4-10). Higher order might bring more accuracy, but comes, for large systems, also at some cost. In some cases, a high order extrapolation is not stable, and the order needs to be reduced.

[

Edit on GitHub

]

FORCE_PAW

:

logical

=

F



Lone keyword:

T

Usage:

FORCE_PAW

Use the GAPW scheme also for atoms with soft basis sets, i.e. the local densities are computed even if hard and soft should be equal. If this keyword is not set to true, those atoms with soft basis sets are treated by a GPW scheme, i.e. the corresponding density contribution goes on the global grid and is expanded in PW. This option nullifies the effect of the GPW_TYPE in the atomic KIND

[

Edit on GitHub

]

GAPW_1C_BASIS

:

enum

=

ORB



Usage:

GAPW_1C_BASIS MEDIUM

Valid values:

ORB

Use orbital basis set.

EXT_SMALL

Extension using Small number of primitive Gaussians.

EXT_MEDIUM

Extension using Medium number of primitive Gaussians.

EXT_LARGE

Extension using Large number of primitive Gaussians.

EXT_VERY_LARGE

Extension using Very Large number of primitive Gaussians.

Specifies how to construct the GAPW one center basis set. Default is to use the primitives from the orbital basis.

[

Edit on GitHub

]

GAPW_ACCURATE_XCINT

:

logical

=

F



Lone keyword:

T

Usage:

GAPW_ACCURATE_XCINT

Use the accurate GAPW/GAPW_XC XC integration scheme for one-center hard/soft density differences. This opt-in path covers regular GAPW/GAPW_XC XC energy, potential, forces, mGGA/tau terms, NLCC, Fine-XC grids, local XC energy-density transfer, analytical stress, TDDFPT/response forces, ADMM-GAPW force paths, an ADMM-GAPW diagonal stress debug path, nonlocal vdW smoke coverage, representative k-point, XAS_TDP, and RTBSE smoke cases, and KG GAPW/GAPW_XC EMBED, EMBED_RI, ATOMIC, and NONE cases. Regular-grid local energy and stress cube print keys keep their existing soft-grid semantics and are not changed by this keyword. The default remains off while this coverage is being prepared for a future default change.

[

Edit on GitHub

]

HIGH_LEVEL_EMBED_SUBSYS

:

logical

=

F



Lone keyword:

T

Usage:

HIGH_LEVEL_EMBED_SUBSYS FALSE

A cluster treated with a high-level method in DFT embedding.

[

Edit on GitHub

]

KG_METHOD

:

logical

=

F



Lone keyword:

T

Usage:

KG_METHOD

References:

Iannuzzi2006

,

Brelaz1979

,

Andermatt2016

Use a Kim-Gordon-like scheme.

[

Edit on GitHub

]

LADDN0

:

integer

=

99



Usage:

LADDN0 integer

GAPW : integer added to the max L of the basis set, used to determine the maximum value of L for the compensation charge density.

[

Edit on GitHub

]

LMAXN0

:

integer

=

2



Aliases:

LMAXRHO0

Usage:

LMAXN0 integer

GAPW : max L number for the expansion compensation densities in spherical gaussians

[

Edit on GitHub

]

LMAXN1

:

integer

=

-1



Aliases:

LMAXRHO1

Usage:

LMAXN1 integer

GAPW : max L number for expansion of the atomic densities in spherical gaussians

[

Edit on GitHub

]

LS_SCF

:

logical

=

F



Lone keyword:

T

Usage:

LS_SCF

Perform a linear scaling SCF

[

Edit on GitHub

]

MAX_RAD_LOCAL

:

real

=

2.50000000E+001



Usage:

MAX_RAD_LOCAL real

GAPW : maximum radius of gaussian functions included in the generation of projectors

[

Edit on GitHub

]

METHOD

:

enum

=

GPW



Usage:

METHOD GAPW

Valid values:

GAPW

Gaussian and augmented plane waves method

GAPW_XC

Gaussian and augmented plane waves method only for XC

GPW

Gaussian and plane waves method

LRIGPW

Local resolution of identity method

RIGPW

Resolution of identity method for HXC terms

MNDO

MNDO semiempirical

MNDOD

MNDO-d semiempirical

AM1

AM1 semiempirical

PM3

PM3 semiempirical

PM6

PM6 semiempirical

PM6-FM

PM6-FM semiempirical

PDG

PDG semiempirical

RM1

RM1 semiempirical

PNNL

PNNL semiempirical

DFTB

DFTB Density Functional based Tight-Binding

XTB

GFN-xTB Extended Tight-Binding

OFGPW

OFGPW Orbital-free GPW method

References:

Lippert1997

,

Lippert1999

,

Krack2000

,

VandeVondele2005

,

VandeVondele2006

,

Dewar1977

,

Dewar1985

,

Rocha2006

,

Stewart1989

,

Thiel1992

,

Repasky2002

,

Stewart2007

,

VanVoorhis2015

,

Chang2008

Mentions:

⭐

X-Ray Absorption from TDDFT

, ⭐

Extended Tight Binding

Specifies the electronic structure method that should be employed

[

Edit on GitHub

]

MIN_PAIR_LIST_RADIUS

:

real

=

0.00000000E+000



Usage:

MIN_PAIR_LIST_RADIUS real

Set the minimum value [Bohr] for the overlap pair list radius. Default is 0.0 Bohr, negative values are changed to the cell size. This allows to control the sparsity of the KS matrix for HFX calculations.

[

Edit on GitHub

]

PW_GRID

:

enum

=

NS-FULLSPACE



Usage:

PW_GRID NS-FULLSPACE

Valid values:

SPHERICAL

not tested

NS-FULLSPACE

tested

NS-HALFSPACE

not tested

What kind of PW_GRID should be employed

[

Edit on GitHub

]

PW_GRID_BLOCKED

:

enum

=

FREE



Usage:

PW_GRID_BLOCKED FREE

Valid values:

FREE

CP2K will select an appropriate value

TRUE

blocked

FALSE

not blocked

Can be used to set the distribution in g-space for the pw grids and their FFT.

[

Edit on GitHub

]

PW_GRID_LAYOUT

:

integer

[

2

]

=

-1



Usage:

PW_GRID_LAYOUT 4 16

Force a particular real-space layout for the plane waves grids. Numbers ≤ 0 mean that this dimension is free, incorrect layouts will be ignored. The default (/-1,-1/) causes CP2K to select a good value, i.e. plane distributed for large grids, more general distribution for small grids.

[

Edit on GitHub

]

QUADRATURE

:

enum

=

GC_LOG



Usage:

QUADRATURE GC_SIMPLE

Valid values:

GC_SIMPLE

Gauss-Chebyshev quadrature

GC_TRANSFORMED

Transformed Gauss-Chebyshev quadrature

GC_LOG

Logarithmic transformed Gauss-Chebyshev quadrature

GAPW: algorithm to construct the atomic radial grids

[

Edit on GitHub

]

REF_EMBED_SUBSYS

:

logical

=

F



Lone keyword:

T

Usage:

REF_EMBED_SUBSYS FALSE

A total, reference, system in DFT embedding.

[

Edit on GitHub

]

STO_NG

:

integer

=

6



Usage:

STO_NG

Order of Gaussian type expansion of Slater orbital basis sets.

[

Edit on GitHub

]

TRANSPORT

:

logical

=

F



Lone keyword:

T

Usage:

TRANSPORT

Perform transport calculations (coupling CP2K and OMEN)

[

Edit on GitHub

]
