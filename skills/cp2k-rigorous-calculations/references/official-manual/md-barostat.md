# CP2K official manual snapshot: md-barostat

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/MOTION/MD/BAROSTAT.html
- Raw SHA-256: d5439ccd02799cb75b43895eda8ed36b95aebbdf2eec2629b8151117ee4cdc83
- Status: version-matched cached official text; reopen the source for current live verification.

BAROSTAT



Parameters of barostat.

[

Edit on GitHub

]

Subsections

MASS

PRINT

THERMOSTAT

VELOCITY

Keywords



PRESSURE

TEMPERATURE

TEMP_TOL

TIMECON

VIRIAL

Keyword descriptions



PRESSURE

:

real

=

0.00000000E+000

[bar]



Usage:

PRESSURE real

Mentions:

⭐

Molecular Dynamics

Initial pressure

[

Edit on GitHub

]

TEMPERATURE

:

real

=

[K]



Usage:

TEMPERATURE real

Barostat initial temperature. If not set, the ensemble temperature is used instead.

[

Edit on GitHub

]

TEMP_TOL

:

real

=

0.00000000E+000

[K]



Usage:

TEMP_TOL real

Maximum oscillation of the Barostat temperature imposed by rescaling.

[

Edit on GitHub

]

TIMECON

:

real

=

1.00000000E+003

[fs]



Usage:

TIMECON real

Mentions:

⭐

Molecular Dynamics

Barostat time constant

[

Edit on GitHub

]

VIRIAL

:

enum

=

XYZ



Usage:

VIRIAL (XYZ | X | Y | Z | XY| XZ | YZ)

Valid values:

XYZ

X

Y

Z

XY

XZ

YZ

Mentions:

⭐

Molecular Dynamics

For NPT_F only: allows the screening of one or more components of the virial in order to relax the cell only along specific cartesian axis

[

Edit on GitHub

]
