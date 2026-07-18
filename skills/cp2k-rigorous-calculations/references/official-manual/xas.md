# CP2K official manual snapshot: xas

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XAS.html
- Raw SHA-256: c253095cab627a11b9ad3dbc8e5c74e0ce53ee0bfb4d8183bc2697b38f107843
- Status: version-matched cached official text; reopen the source for current live verification.

XAS



References:

Iannuzzi2007

Controls transition-potential and delta-SCF calculations of core-level excitation spectra. The occupied states from which the excitations are calculated should be specified. Localization of the orbitals may be useful.

[

Edit on GitHub

]

Subsections

LOCALIZE

PRINT

SCF

Keywords



SECTION_PARAMETERS

ADDED_MOS

ATOMS_LIST

DIPOLE_FORM

EPS_ADDED

MAX_ITER_ADDED

METHOD

NGAUSS

ORBITAL_LIST

OVERLAP_THRESHOLD

RESTART

SPIN_CHANNEL

STATE_SEARCH

STATE_TYPE

WFN_RESTART_FILE_NAME

XAS_CORE

XAS_TOT_EL

XES_CORE

XES_EMPTY_HOMO

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

&XAS T

controls the activation of core-level spectroscopy simulations

[

Edit on GitHub

]

ADDED_MOS

:

integer

=

-1



Usage:

ADDED_MOS {integer}

Number of additional MOS added spin up only

[

Edit on GitHub

]

ATOMS_LIST

:

integer[

]



Keyword can be repeated.

Aliases:

AT_LIST

Usage:

ATOMS_LIST {integer} {integer} .. {integer}

Indexes of the atoms to be excited. This keyword can be repeated several times (useful if you have to specify many indexes).

[

Edit on GitHub

]

DIPOLE_FORM

:

enum

=

VELOCITY



Aliases:

DIP_FORM

Usage:

DIPOLE_FORM string

Valid values:

LENGTH

Length form ⟨ i | e r | j ⟩

VELOCITY

Velocity form ⟨ i | d/dr | j ⟩

Type of integral to get the oscillator strengths in the diipole approximation

[

Edit on GitHub

]

EPS_ADDED

:

real

=

1.00000000E-005



Usage:

EPS_ADDED 1.e-6

target accuracy incalculation of the added orbitals

[

Edit on GitHub

]

MAX_ITER_ADDED

:

integer

=

2999



Usage:

MAX_ITER_ADDED 100

maximum number of iteration in calculation of added orbitals

[

Edit on GitHub

]

METHOD

:

enum

=

NONE



Aliases:

XAS_METHOD

Usage:

METHOD TP_HH

Valid values:

NONE

No core electron spectroscopy

TP_HH

Transition potential half-hole

TP_FH

Transition potential full-hole

TP_VAL

Hole in homo for X-ray emission only

TP_XHH

Transition potential excited half-hole

TP_XFH

Transition potential excited full-hole

DSCF

DSCF calculations to compute the first (core)excited state

TP_FLEX

Transition potential with generalized core occupation and total number of electrons

Method to be used to calculate core-level excitation spectra

[

Edit on GitHub

]

NGAUSS

:

integer

=

3



Usage:

NGAUSS {integer}

Number of gto’s for the expansion of the STO of the type given by STATE_TYPE

[

Edit on GitHub

]

ORBITAL_LIST

:

integer[

]



Keyword can be repeated.

Aliases:

ORBITAL_LIST

Usage:

ORBITAL_LIST {integer} {integer} .. {integer}

Indices of the localized orbitals to be excited. This keyword can be repeated several times (useful if you have to specify many indexes).

[

Edit on GitHub

]

OVERLAP_THRESHOLD

:

real

=

1.00000000E+000



Usage:

OVERLAP_THRESHOLD 8.e-1

Threshold for including more than one initial core excited state per atom. The threshold is taken relative to the maximum overlap.

[

Edit on GitHub

]

RESTART

:

logical

=

F



Lone keyword:

T

Usage:

RESTART

Restart the excited state if the restart file exists

[

Edit on GitHub

]

SPIN_CHANNEL

:

integer

=

1



Usage:

SPIN_CHANNEL 1

# Spin channel of the excited orbital

[

Edit on GitHub

]

STATE_SEARCH

:

integer

=

-1



Usage:

STATE_SEARCH 1

# of states where to look for the one to be excited

[

Edit on GitHub

]

STATE_TYPE

:

enum

=

1S



Aliases:

TYPE

Usage:

STATE_TYPE 1S

Valid values:

1S

1s orbitals

2S

2s orbitals

2P

2p orbitals

3S

3s orbitals

3P

3p orbitals

3D

3d orbitals

4S

4s orbitals

4P

4p orbitals

4D

4d orbitals

4F

4f orbitals

Type of the orbitals that are excited for the xas spectra calculation

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

Root of the file names where to read the MOS from which to restart the calculation of the core level excited states

[

Edit on GitHub

]

XAS_CORE

:

real

=

5.00000000E-001



Usage:

XAS_CORE 0.5

Occupation of the core state in XAS calculation by TP_FLEX.

[

Edit on GitHub

]

XAS_TOT_EL

:

real

=

-1.00000000E+000



Usage:

XAS_TOT_EL 10

Total number of electrons for spin channel alpha, in XAS calculation by TP_FLEX. If it is a negative value, the number of electrons is set to GS number of electrons minus the amount subtracted from the core state

[

Edit on GitHub

]

XES_CORE

:

real

=

1.00000000E+000



Usage:

XES_CORE 0.5

Occupation of the core state in XES calculation by TP_VAL. The HOMO is emptied by the same amount.

[

Edit on GitHub

]

XES_EMPTY_HOMO

:

logical

=

F



Lone keyword:

T

Usage:

XES_EMPTY_HOMO

Set the occupation of the HOMO in XES calculation by TP_VAL. The HOMO can be emptied or not, if the core is still full.

[

Edit on GitHub

]
