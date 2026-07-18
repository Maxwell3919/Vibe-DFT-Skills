# CP2K official manual snapshot: dft

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT.html
- Raw SHA-256: 3b882b74509d0ba7dd7984bebbe2ceef3d00bc24d42460727842c25c466824fb
- Status: version-matched cached official text; reopen the source for current live verification.

DFT



Controls electronic-structure settings for Quickstep and related Gaussian-basis DFT methods.

[

Edit on GitHub

]

Subsections

ACTIVE_SPACE

ALMO_SCF

AUXILIARY_DENSITY_MATRIX_METHOD

DENSITY_FITTING

EFIELD

ENERGY_CORRECTION

EXCITED_STATES

EXTERNAL_DENSITY

EXTERNAL_POTENTIAL

EXTERNAL_VXC

HAIRY_PROBES

HARRIS_METHOD

KG_METHOD

KPOINTS

KPOINT_SET

LOCALIZE

LOW_SPIN_ROKS

LS_SCF

MGRID

PERIODIC_EFIELD

PLANAR_AVERAGED_V_HARTREE

PLANAR_COUNTER_CHARGE

POISSON

PRINT

QS

REAL_TIME_PROPAGATION

RELATIVISTIC

SCCS

SCF

SCRF

SIC

SMEAGOL

TRANSPORT

XAS

XAS_TDP

XC

Keywords



AUTO_BASIS

BASIS_SET_FILE_NAME

CHARGE

CORE_CORR_DIP

MULTIPLICITY

PLUS_U_METHOD

POTENTIAL_FILE_NAME

RELAX_MULTIPLICITY

ROKS

SORT_BASIS

SUBCELLS

SURFACE_DIPOLE_CORRECTION

SURF_DIP_DIR

SURF_DIP_POS

SURF_DIP_SWITCH

UKS

WFN_RESTART_FILE_NAME

Keyword descriptions



AUTO_BASIS

:

string[

]

=

X



Keyword can be repeated.

Usage:

AUTO_BASIS {basis_type} {basis_size}

Mentions:

⭐

Preliminaries

, ⭐

X-Ray Absorption from TDDFT

Specify size of automatically generated auxiliary (RI) basis sets: Options={small,medium,large,huge}

[

Edit on GitHub

]

BASIS_SET_FILE_NAME

:

string

=

BASIS_SET



Keyword can be repeated.

Usage:

BASIS_SET_FILE_NAME

Mentions:

⭐

Basis Sets

Name of a basis-set library file, optionally including a path. This keyword can be repeated to search several basis-set files.

[

Edit on GitHub

]

CHARGE

:

integer

=

0



Usage:

CHARGE -1

Mentions:

⭐

Troubleshooting

, ⭐

How to make a SCF run converge

, ⭐

RESP Charges

The total charge of the system

[

Edit on GitHub

]

CORE_CORR_DIP

:

logical

=

F



Lone keyword:

T

Usage:

CORE_CORR_DIP .TRUE.

If the total CORE_CORRECTION is non-zero and surface dipole correction is switched on, presence of this keyword will adjust electron density via MO occupation to reflect the total CORE_CORRECTION. The default value is .FALSE.

[

Edit on GitHub

]

MULTIPLICITY

:

integer

=

0



Aliases:

MULTIP

Usage:

MULTIPLICITY 3

Mentions:

⭐

Troubleshooting

, ⭐

How to make a SCF run converge

Two times the total spin plus one. Specify 3 for a triplet, 4 for a quartet, and so on. Default is 1 (singlet) for an even number and 2 (doublet) for an odd number of electrons.

[

Edit on GitHub

]

PLUS_U_METHOD

:

enum

=

MULLIKEN



Usage:

PLUS_U_METHOD Lowdin

Valid values:

LOWDIN

Method based on Lowdin population analysis (computationally expensive, since the diagonalization of the overlap matrix is required, but possibly more robust than Mulliken)

MULLIKEN

Method based on Mulliken population analysis using the net AO and overlap populations (computationally cheap method)

MULLIKEN_CHARGES

Method based on Mulliken gross orbital populations (GOP)

Method employed for the calculation of the DFT+U contribution

[

Edit on GitHub

]

POTENTIAL_FILE_NAME

:

string

=

POTENTIAL



Usage:

POTENTIAL_FILE_NAME

Mentions:

⭐

Pseudopotentials

Name of the pseudopotential library file, optionally including a path. The potential selected for each kind is set with KIND%POTENTIAL.

[

Edit on GitHub

]

RELAX_MULTIPLICITY

:

real

=

0.00000000E+000



Aliases:

RELAX_MULTIP

Usage:

RELAX_MULTIPLICITY 0.00001

Tolerance in Hartrees. Do not enforce the occupation of alpha and beta MOs due to the initially defined multiplicity, but rather follow the Aufbau principle. A value greater than zero activates this option. If alpha/beta MOs differ in energy less than this tolerance, then alpha-MO occupation is preferred even if it is higher in energy (within the tolerance). Such spin-symmetry broken (spin-polarized) occupation is used as SCF input, which (is assumed to) bias the SCF towards a spin-polarized solution. Thus, larger tolerance increases chances of ending up with spin-polarization. This option is only valid for unrestricted (i.e. spin polarised) Kohn-Sham (UKS) calculations. It also needs non-zero

ADDED_MOS

to actually affect the calculations, which is why it is not expected to work with

OT

and may raise errors when used with OT. For more details see

this discussion

.

[

Edit on GitHub

]

ROKS

:

logical

=

F



Aliases:

RESTRICTED_OPEN_KOHN_SHAM

Lone keyword:

T

Usage:

ROKS

Requests a restricted open Kohn-Sham calculation

[

Edit on GitHub

]

SORT_BASIS

:

enum

=

DEFAULT



Usage:

SORT_BASIS EXP

Valid values:

DEFAULT

don’t sort

EXP

sort w.r.t. exponent

Mentions:

⭐

HFX-RI for Γ-Point (non-periodic)

Sorts basis functions according to a selected criterion. Sorting by exponent can improve data locality for selected exact-exchange and RI workflows.

[

Edit on GitHub

]

SUBCELLS

:

real

=

2.00000000E+000



Usage:

SUBCELLS 1.5

Read the grid size for subcell generation in the construction of neighbor lists.

[

Edit on GitHub

]

SURFACE_DIPOLE_CORRECTION

:

logical

=

F



Aliases:

SURFACE_DIPOLE ,SURF_DIP

Lone keyword:

T

Usage:

SURF_DIP

References:

Bengtsson1999

For slab calculations with asymmetric geometries, activate the correction of the electrostatic potential with by compensating for the surface dipole. Implemented only for slabs with normal parallel to one Cartesian axis. The normal direction is given by the keyword SURF_DIP_DIR

[

Edit on GitHub

]

SURF_DIP_DIR

:

enum

=

Z



Usage:

SURF_DIP_DIR Z

Valid values:

X

Along x

Y

Along y

Z

Along z

Cartesian axis parallel to surface normal.

[

Edit on GitHub

]

SURF_DIP_POS

:

real

=

-1.00000000E+000



Usage:

SURF_DIP_POS -1.0_dp

This keyword assigns an user defined position in Angstroms in the direction normal to the surface (given by SURF_DIP_DIR). The default value is -1.0_dp which appplies the correction at a position that has minimum electron density on the grid.

[

Edit on GitHub

]

SURF_DIP_SWITCH

:

logical

=

F



Lone keyword:

T

Usage:

SURF_DIP_SWITCH .TRUE.

WARNING: Experimental feature under development that will help the user to switch parameters to facilitate SCF convergence. In its current form the surface dipole correction is switched off if the calculation does not converge in (0.5*MAX_SCF + 1) outer_scf steps. The default value is .FALSE.

[

Edit on GitHub

]

UKS

:

logical

=

F



Aliases:

UNRESTRICTED_KOHN_SHAM ,LSD ,SPIN_POLARIZED

Lone keyword:

T

Usage:

LSD

Mentions:

⭐

Troubleshooting

, ⭐

How to make a SCF run converge

, ⭐

Extended Tight Binding

Requests a spin-polarized calculation using alpha and beta orbitals, i.e. no spin restriction is applied

[

Edit on GitHub

]

WFN_RESTART_FILE_NAME

:

string



Aliases:

RESTART_FILE_NAME

Usage:

WFN_RESTART_FILE_NAME

Mentions:

⭐

How to make a SCF run converge

, ⭐

Real-Time Propagation and Ehrenfest MD

Name of the wavefunction restart file, may include a path. If no file is specified, the default is to open the file as generated by the wfn restart print key.

[

Edit on GitHub

]
