# CP2K official manual snapshot: vibrational-analysis

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/VIBRATIONAL_ANALYSIS.html
- Raw SHA-256: 74344c15ab1a3e19785a7a5bc86aebd05622fda8412c4bb9b389424c4dcbd442
- Status: version-matched cached official text; reopen the source for current live verification.

VIBRATIONAL_ANALYSIS



Section to setup parameters to perform a Normal Modes, vibrational, or phonon analysis. Vibrations are computed using finite differences, which implies a very tight (e.g. 1E-8) threshold is needed for EPS_SCF to get accurate low frequencies. The analysis assumes a stationary state (minimum or TS), i.e. tight geometry optimization (MAX_FORCE) is needed as well.

[

Edit on GitHub

]

Subsections

MODE_SELECTIVE

PRINT

Keywords



DX

FULLY_PERIODIC

INTENSITIES

NPROC_REP

PROC_DIST_TYPE

TC_PRESSURE

TC_TEMPERATURE

THERMOCHEMISTRY

Keyword descriptions



DX

:

real

=

1.00000000E-002

[bohr]



Specify the increment to be used to construct the HESSIAN with finite difference method

[

Edit on GitHub

]

FULLY_PERIODIC

:

logical

=

F



Lone keyword:

T

Avoids to clean rotations from the Hessian matrix.

[

Edit on GitHub

]

INTENSITIES

:

logical

=

F



Lone keyword:

T

Calculation of the IR/Raman-Intensities. Calculation of dipoles and/or polarizabilities have to be specified explicitly in DFT/PRINT/MOMENTS and/or PROPERTIES/LINRES/POLAR

[

Edit on GitHub

]

NPROC_REP

:

integer

=

1



Mentions:

⭐

Simulating Vibronic Effects in Optical Spectra

Specify the number of processors to be used per replica environment (for parallel runs). In case of mode selective calculations more than one replica will start a block Davidson algorithm to track more than only one frequency

[

Edit on GitHub

]

PROC_DIST_TYPE

:

enum

=

BLOCKED



Usage:

PROC_DIST_TYPE (INTERLEAVED|BLOCKED)

Valid values:

INTERLEAVED

Interleaved distribution

BLOCKED

Blocked distribution

Specify the topology of the mapping of processors into replicas.

[

Edit on GitHub

]

TC_PRESSURE

:

real

=

1.01325000E+005

[Pa]



Pressure for the calculation of the thermochemical data

[

Edit on GitHub

]

TC_TEMPERATURE

:

real

=

2.73150000E+002

[K]



Usage:

tc_temperature 325.0

Temperature for the calculation of the thermochemical data

[

Edit on GitHub

]

THERMOCHEMISTRY

:

logical

=

F



Lone keyword:

T

Calculation of the thermochemical data. Valid for molecules in the gas phase, not supporting phonon frequencies at general

q

-points beyond wave vector

q

at gamma point. Based on the rigid-rotor harmonic oscillator (RRHO) model, which is known to break down if very low vibrational frequencies are present in a flexible system.

[

Edit on GitHub

]
