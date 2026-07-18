# CP2K official manual snapshot: kind

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/SUBSYS/KIND.html
- Raw SHA-256: 213be6984fa2ce2cee4701b5c86a80e10f1efba526074e3cfb4d06f5df93e16e
- Status: version-matched cached official text; reopen the source for current live verification.

KIND



Section can be repeated.

Defines settings shared by atoms of the same kind, such as basis sets, pseudopotentials, all-electron treatment, and atom-centered grids.

[

Edit on GitHub

]

Subsections

BASIS

BS

DFT_PLUS_U

KG_POTENTIAL

PAO_DESCRIPTOR

PAO_POTENTIAL

POTENTIAL

Keywords



SECTION_PARAMETERS

BASIS_SET

CORE_CORRECTION

COVALENT_RADIUS

DFTB3_PARAM

ECP_SEMI_LOCAL

ELEC_CONF

ELEMENT

FLOATING_BASIS_CENTER

GHOST

GPW_TYPE

HARD_EXP_RADIUS

KG_POTENTIAL

KG_POTENTIAL_FILE_NAME

LEBEDEV_GRID

LMAX_DFTB

MAGNETIZATION

MAO

MASS

MAX_RAD_LOCAL

MM_RADIUS

MONOVALENT

NO_OPTIMIZE

PAO_BASIS_SIZE

PAO_MODEL_FILE

POTENTIAL

POTENTIAL_FILE_NAME

POTENTIAL_TYPE

RADIAL_GRID

RHO0_EXP_RADIUS

SE_P_ORBITALS_ON_H

VDW_RADIUS

Keyword descriptions



SECTION_PARAMETERS

:

string

=

DEFAULT



Usage:

H

The name of the kind described in this section.

[

Edit on GitHub

]

BASIS_SET

:

string[

]



Keyword can be repeated.

Usage:

BASIS_SET [type] [form] DZVP

References:

VandeVondele2005

,

VandeVondele2007

Mentions:

⭐

Basis Sets

, ⭐

Band structure from GW

, ⭐

Preliminaries

, ⭐

GW + Bethe-Salpeter equation

Selects a Gaussian basis set for this kind. The default type is ORB and the default form is GTO; NONE implies no basis and is meaningful for ghost atoms. Possible values for TYPE are {ORB, AUX, MIN, RI_AUX, LRI, …}. Possible values for FORM are {GTO, STO}. Where STO results in a GTO expansion of a Slater type basis. If a value for FORM is given, also TYPE has to be set explicitly.

[

Edit on GitHub

]

CORE_CORRECTION

:

real

=

0.00000000E+000



Usage:

CORE_CORRECTION 1.0

Corrects the effective nuclear charge

[

Edit on GitHub

]

COVALENT_RADIUS

:

real

=

0.00000000E+000

[angstrom]



Usage:

COVALENT_RADIUS 1.24

Use this covalent radius (in Angstrom) for all atoms of the atomic kind instead of the internally tabulated default value

[

Edit on GitHub

]

DFTB3_PARAM

:

real

=

0.00000000E+000



Usage:

DFTB3_PARAM 0.2

The third order parameter (derivative of hardness) used in diagonal DFTB3 correction.

[

Edit on GitHub

]

ECP_SEMI_LOCAL

:

logical

=

T



Lone keyword:

T

Usage:

ECP_SEMI_LOCAL {T,F}

Use ECPs in the original semi-local form. This requires the availability of the corresponding integral library. If set to False, a fully nonlocal one-center expansion of the ECP is constructed.

[

Edit on GitHub

]

ELEC_CONF

:

integer[

]



Usage:

ELEC_CONF n_elec(s) n_elec(p) n_elec(d) …

Specifies the electronic configuration used in construction the atomic initial guess (see the pseudo potential file for the default values).

[

Edit on GitHub

]

ELEMENT

:

string



Aliases:

ELEMENT_SYMBOL

Usage:

ELEMENT O

The element of the actual kind (if not given it is inferred from the kind name)

[

Edit on GitHub

]

FLOATING_BASIS_CENTER

:

logical

=

F



Lone keyword:

T

Usage:

FLOATING_BASIS_CENTER

This keyword makes all atoms of this kind floating functions, i.e. without pseudo or nuclear charge which are subject to a geometry optimization in the outer SCF.

[

Edit on GitHub

]

GHOST

:

logical

=

F



Lone keyword:

T

Usage:

GHOST

Mentions:

⭐

Preliminaries

This keyword makes all atoms of this kind ghost atoms, i.e. without pseudo or nuclear charge. Useful to just have the basis set at that position (e.g. BSSE calculations), or to have a non-interacting particle with BASIS_SET NONE

[

Edit on GitHub

]

GPW_TYPE

:

logical

=

F



Lone keyword:

T

Usage:

GPW_TYPE

Force one type to be treated by the GPW scheme, whatever are its primitives, even if the GAPW method is used

[

Edit on GitHub

]

HARD_EXP_RADIUS

:

real



Usage:

HARD_EXP_RADIUS 0.9

The region where the hard density is supposed to be confined (GAPW) (in Bohr, default is 1.2 for H and 1.512 otherwise)

[

Edit on GitHub

]

KG_POTENTIAL

:

string

=

NONE



Aliases:

KG_POT

Usage:

KG_POTENTIAL

The name of the non-additive atomic kinetic energy potential.

[

Edit on GitHub

]

KG_POTENTIAL_FILE_NAME

:

string

=

-



Usage:

KG_POTENTIAL_FILE_NAME

The name of the file where to find this kinds KG potential. Default file is specified in DFT section.

[

Edit on GitHub

]

LEBEDEV_GRID

:

integer

=

50



Usage:

LEBEDEV_GRID 40

Mentions:

⭐

Gaussian Augmented Plane Waves

GAPW: size of the angular Lebedev grid used for atom-centered integrations for this kind.

[

Edit on GitHub

]

LMAX_DFTB

:

integer

=

-1



Usage:

LMAX_DFTB 1

The maximum l-quantum number of the DFTB basis for this kind.

[

Edit on GitHub

]

MAGNETIZATION

:

real

=

0.00000000E+000



Usage:

MAGNETIZATION 0.5

Mentions:

⭐

How to make a SCF run converge

The magnetization used in the atomic initial guess. Adds magnetization/2 spin-alpha electrons and removes magnetization/2 spin-beta electrons.

[

Edit on GitHub

]

MAO

:

integer

=

-1



Usage:

MAO 4

The number of MAOs (Modified Atomic Orbitals) for this kind.

[

Edit on GitHub

]

MASS

:

real



Aliases:

ATOMIC_MASS ,ATOMIC_WEIGHT ,WEIGHT

Usage:

MASS 2.0

The mass of the atom (if negative or non present it is inferred from the element symbol)

[

Edit on GitHub

]

MAX_RAD_LOCAL

:

real

=

2.45664397E+001



Usage:

MAX_RAD_LOCAL 15.0

Max radius for the basis functions used to generate the local projectors in GAPW [Bohr]

[

Edit on GitHub

]

MM_RADIUS

:

real

=

0.00000000E+000

[angstrom]



Usage:

MM_RADIUS {real}

Defines the radius of the electrostatic multipole of the atom in Fist. This radius applies to the charge, the dipole and the quadrupole. When zero, the atom is treated as a point multipole, otherwise it is treated as a Gaussian charge distribution with the given radius: p(x,y,z)

N

exp(-(x

2+y

2+z

2)/(2*MM_RADIUS

2)), where N is a normalization constant. In the core-shell model, only the shell is treated as a Gaussian and the core is always a point charge.

[

Edit on GitHub

]

MONOVALENT

:

logical

=

F



Lone keyword:

T

Usage:

MONOVALENT

This keyword makes all atoms of this kind monovalent, i.e. with a single electron and nuclear charge set to 1.0. Used to saturate dangling bonds, ideally in conjunction with a monovalent pseudopotential. Currently GTH only.

[

Edit on GitHub

]

NO_OPTIMIZE

:

logical

=

F



Lone keyword:

T

Usage:

NO_OPTIMIZE

Skip optimization of this type (used in specific basis set or potential optimization schemes)

[

Edit on GitHub

]

PAO_BASIS_SIZE

:

integer

=

0



Mentions:

⭐

PAO-ML

The block size used for the polarized atomic orbital basis. Setting PAO_BASIS_SIZE to the size of the primary basis or to a value below one will disables the PAO method for the given atomic kind. By default PAO is disbabled.

[

Edit on GitHub

]

PAO_MODEL_FILE

:

string



The filename of the PyTorch model for predicting PAO basis sets.

[

Edit on GitHub

]

POTENTIAL

:

string[

]



Aliases:

POT

Usage:

POTENTIAL [type]

References:

Goedecker1996

,

Hartwigsen1998

,

Krack2005

Mentions:

⭐

Pseudopotentials

The type (ECP, ALL, GTH, UPS) and name of the pseudopotential for the defined kind. Use GTH potentials for most GPW calculations, ECP for Gaussian-integral effective core potentials, and ALL for all-electron calculations.

[

Edit on GitHub

]

POTENTIAL_FILE_NAME

:

string

=

-



Usage:

POTENTIAL_FILE_NAME

The name of the file where to find this kinds pseudopotential. Default file is specified in DFT section.

[

Edit on GitHub

]

POTENTIAL_TYPE

:

string



Usage:

POTENTIAL_TYPE

The type of this kinds pseudopotential (ECP, ALL, GTH, UPS).

[

Edit on GitHub

]

Warning

The keyword

POTENTIAL_TYPE

is deprecated and may be removed in a future version.

Use ‘POTENTIAL

…’ instead.

RADIAL_GRID

:

integer

=

50



Usage:

RADIAL_GRID 70

Mentions:

⭐

Gaussian Augmented Plane Waves

GAPW: number of radial grid points used for atom-centered integrations for this kind.

[

Edit on GitHub

]

RHO0_EXP_RADIUS

:

real



Usage:

RHO0_EXP_RADIUS 0.9

the radius which defines the atomic region where the hard compensation density is confined. should be less than HARD_EXP_RADIUS (GAPW) (Bohr, default equals HARD_EXP_RADIUS)

[

Edit on GitHub

]

SE_P_ORBITALS_ON_H

:

logical

=

F



Lone keyword:

T

Usage:

SE_P_ORBITALS_ON_H

Forces the usage of p-orbitals on H for SEMI-EMPIRICAL calculations. This keyword applies only when the KIND is specifying an Hydrogen element. It is ignored in all other cases.

[

Edit on GitHub

]

VDW_RADIUS

:

real

=

0.00000000E+000

[angstrom]



Usage:

VDW_RADIUS 1.85

Use this van der Waals radius (in Angstrom) for all atoms of the atomic kind instead of the internally tabulated default value

[

Edit on GitHub

]
